local base = import 'base.libsonnet';
local volumes = import 'volumes.libsonnet';

local ingress(metadata) = base.Ingress(metadata, 'https-ingress') {
  metadata+: {
    annotations: {
      'kubernetes.io/ingress.global-static-ip-name': metadata.backend.ipName,
      'kubernetes.io/ingress.allow-http': 'false',
    },
  },
  spec: {
    defaultBackend: {
      service: {
        name: 'core-service',
        port: {
          number: metadata.backend.port,
        }
      }
    },
  },
};

{
  ManagedCertIngress(metadata): {
    ingress: ingress(metadata) {
      metadata+: {
        annotations+: {
          'networking.gke.io/managed-certificates': 'https-certificate',
        },
      },
    },
    managedCert: base.ManagedCert(metadata, 'https-certificate') {
      spec: {
        domains: [
          metadata.backend.hostname,
        ],
      },
    },
  },

  PresharedCertIngress(metadata, certName): ingress(metadata) {
    metadata+: {
      annotations+: {
        'ingress.gcp.kubernetes.io/pre-shared-cert': certName,
      },
    },
  },

  all(metadata): {
    ingress: $.ManagedCertIngress(metadata),
    service: base.Service(metadata, 'core-service') {
      app:: 'core-service',
      port:: metadata.backend.port,
      type:: 'NodePort',
      enable_monitoring:: false,
    },

    deployment: base.Deployment(metadata, 'core-service') {
      apiVersion: 'apps/v1',
      kind: 'Deployment',
      metadata+: {
        namespace: metadata.namespace,
      },
      spec+: {
        template+: {
          spec+: {
            volumes: volumes.backendVolumes,
            soloContainer:: base.Container('core-service') {
              image: metadata.backend.image,
              imagePullPolicy: 'Always',
              ports: [
                {
                  containerPort: metadata.backend.port,
                  name: 'http',
                },
              ],
              volumeMounts: volumes.backendMounts,
              command: ['core-service'],
              args_:: {
                addr: ':' + metadata.backend.port,
                gcp_prof_service_name: metadata.backend.prof_grpc_name,
                cockroach_host: 'cockroachdb-balanced.' + metadata.namespace,
                cockroach_port: metadata.cockroach.grpc_port,
                cockroach_ssl_mode: 'verify-full',
                cockroach_user: 'root',
                cockroach_ssl_dir: '/cockroach/cockroach-certs',
                garbage_collector_spec: '@every 30m',
                public_key_files: std.join(",", metadata.backend.pubKeys),
                jwks_endpoint: metadata.backend.jwksEndpoint,
                jwks_key_ids: std.join(",", metadata.backend.jwksKeyIds),
                dump_requests: metadata.backend.dumpRequests,
                accepted_jwt_audiences: metadata.backend.hostname,
                locality: metadata.cockroach.locality,
                enable_scd: metadata.enableScd,
              },
              readinessProbe: {
                httpGet: {
                  path: '/healthy',
                  port: metadata.backend.port,
                },
              },
            },
          },
        },
      },
    },
  },
}
