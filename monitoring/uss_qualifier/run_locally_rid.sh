#!/usr/bin/env bash

set -eo pipefail

# Find and change to repo root directory
OS=$(uname)
if [[ "$OS" == "Darwin" ]]; then
	# OSX uses BSD readlink
	BASEDIR="$(dirname "$0")"
else
	BASEDIR=$(readlink -e "$(dirname "$0")")
fi
cd "${BASEDIR}/../.." || exit 1

echo '#########################################################################'
echo '## NOTE: A prerequisite for running this command locally is to have    ##'
echo '## running instances of mock_uss acting as RID SP and RID DP           ##'
echo '## (../mock_uss/run_locally_ridsp.sh) and                              ##'
echo '## (../mock_uss/run_locally_riddp.sh) including related dependencies.  ##'
echo '#########################################################################'

monitoring/build.sh || exit 1

CONFIG_LOCATION="monitoring/uss_qualifier/config_run_locally_rid.json"
CONFIG='--config config_run_locally_rid.json'

AUTH='--auth DummyOAuth(http://host.docker.internal:8085/token,uss_qualifier)'

echo '{
    "locale": "CHE",
    "rid": {
      "injection_targets": [
        {
          "name": "uss1",
          "injection_base_url": "http://host.docker.internal:8071/ridsp/injection"
        }
      ],
      "observers": [
        {
          "name": "uss2",
          "observation_base_url": "http://host.docker.internal:8073/riddp/observation"
        }
      ]
    }
}' > ${CONFIG_LOCATION}

QUALIFIER_OPTIONS="$AUTH $CONFIG"

REPORT_FILE="$(pwd)/monitoring/uss_qualifier/report_rid.json"
# Report file must already exist to share correctly with the Docker container
touch "${REPORT_FILE}"

if [ "$CI" == "true" ]; then
  docker_args="--add-host host.docker.internal:host-gateway" # Required to reach other containers in Ubuntu (used for Github Actions)
else
  docker_args="-it"
fi

# shellcheck disable=SC2086
docker run ${docker_args} --name uss_qualifier \
  --rm \
  -e QUALIFIER_OPTIONS="${QUALIFIER_OPTIONS}" \
  -e PYTHONBUFFERED=1 \
  -v "${REPORT_FILE}:/app/monitoring/uss_qualifier/report_rid.json" \
  -v "$(pwd):/app" \
  -w /app/monitoring/uss_qualifier \
  interuss/monitoring \
  python main.py $QUALIFIER_OPTIONS

rm ${CONFIG_LOCATION}
