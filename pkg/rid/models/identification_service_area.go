package models

import (
	"time"

	"github.com/golang/geo/s2"
	"github.com/interuss/dss/pkg/api/v1/ridpb"
	dsserr "github.com/interuss/dss/pkg/errors"
	"github.com/interuss/dss/pkg/geo"
	dssmodels "github.com/interuss/dss/pkg/models"
	"github.com/interuss/stacktrace"
	"google.golang.org/protobuf/proto"
	tspb "google.golang.org/protobuf/types/known/timestamppb"
)

// IdentificationServiceArea represents a USS ISA over a given 4D volume.
type IdentificationServiceArea struct {
	ID         dssmodels.ID
	URL        string
	Owner      dssmodels.Owner
	Cells      s2.CellUnion
	StartTime  *time.Time
	EndTime    *time.Time
	Version    *dssmodels.Version
	AltitudeHi *float32
	AltitudeLo *float32
	Writer     string
}

// SetCells is a convenience function that accepts an int64 array and converts
// to s2.CellUnion.
// TODO: wrap s2.CellUnion in a custom type that embeds the struct such that
// we can still call its function directly, but also implements scan for sql
// driver.
func (i *IdentificationServiceArea) SetCells(cids []int64) {
	i.Cells = geo.CellUnionFromInt64(cids)
}

// ToProto converts an IdentificationServiceArea struct to an
// IdentificationServiceArea proto for API consumption.
func (i *IdentificationServiceArea) ToProto() (*ridpb.IdentificationServiceArea, error) {
	result := &ridpb.IdentificationServiceArea{
		Id:         i.ID.String(),
		Owner:      i.Owner.String(),
		FlightsUrl: i.URL,
		Version:    i.Version.String(),
	}

	if i.StartTime != nil {
		ts := tspb.New(*i.StartTime)
		result.TimeStart = ts
	}

	if i.EndTime != nil {
		ts := tspb.New(*i.EndTime)
		result.TimeEnd = ts
	}
	return result, nil
}

// SetExtents performs some data validation and sets the 4D volume on the
// IdentificationServiceArea.
func (i *IdentificationServiceArea) SetExtents(extents *ridpb.Volume4D) error {
	var err error
	if extents == nil {
		return nil
	}
	if startTime := extents.GetTimeStart(); startTime != nil {
		ts := startTime.AsTime()
		err := startTime.CheckValid()
		if err != nil {
			return stacktrace.Propagate(err, "Error converting start time from proto")
		}
		i.StartTime = &ts
	}

	if endTime := extents.GetTimeEnd(); endTime != nil {
		ts := endTime.AsTime()
		err := endTime.CheckValid()
		if err != nil {
			return stacktrace.Propagate(err, "Error converting end time from proto")
		}
		i.EndTime = &ts
	}

	space := extents.GetSpatialVolume()
	if space == nil {
		return stacktrace.NewError("Missing required spatial_volume")
	}
	i.AltitudeHi = proto.Float32(space.GetAltitudeHi())
	i.AltitudeLo = proto.Float32(space.GetAltitudeLo())
	footprint := space.GetFootprint()
	if footprint == nil {
		return stacktrace.NewError("spatial_volume missing required footprint")
	}
	i.Cells, err = dssmodels.GeoPolygonFromRIDProto(footprint).CalculateCovering()
	if err != nil {
		return stacktrace.Propagate(err, "Error calculating covering from polygon")
	}
	return nil
}

// AdjustTimeRange adjusts the time range to the max allowed ranges on a
// IdentificationServiceArea.
func (i *IdentificationServiceArea) AdjustTimeRange(now time.Time, old *IdentificationServiceArea) error {
	if i.StartTime == nil {
		// If StartTime was omitted, default to Now() for new ISAs or re-
		// use the existing time of existing ISAs.
		if old == nil {
			i.StartTime = &now
		} else {
			i.StartTime = old.StartTime
		}
	} else {
		// If setting the StartTime explicitly ensure it is not too far in the past.
		if now.Sub(*i.StartTime) > maxClockSkew {
			return stacktrace.NewErrorWithCode(dsserr.BadRequest, "IdentificationServiceArea time_start must not be in the past")
		}
	}

	// If EndTime was omitted default to the existing ISA's EndTime.
	if i.EndTime == nil && old != nil {
		i.EndTime = old.EndTime
	}

	// EndTime cannot be omitted for new ISAs.
	if i.EndTime == nil {
		return stacktrace.NewErrorWithCode(dsserr.BadRequest, "IdentificationServiceArea must have an time_end")
	}

	// EndTime cannot be before StartTime.
	if i.EndTime.Sub(*i.StartTime) < 0 {
		return stacktrace.NewErrorWithCode(dsserr.BadRequest, "IdentificationServiceArea time_end must be after time_start")
	}

	return nil
}
