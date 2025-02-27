from __future__ import annotations

from datetime import timedelta
from typing import List, Union

import pydantic
from typing_extensions import Literal

from datahub.api.entities.datacontract.assertion import BaseAssertion
from datahub.configuration.common import ConfigModel
from datahub.emitter.mcp import MetadataChangeProposalWrapper
from datahub.metadata.schema_classes import (
    AssertionInfoClass,
    AssertionTypeClass,
    CalendarIntervalClass,
    FixedIntervalScheduleClass,
    FreshnessAssertionInfoClass,
    FreshnessAssertionScheduleClass,
    FreshnessAssertionScheduleTypeClass,
    FreshnessAssertionTypeClass,
    FreshnessCronScheduleClass,
)


class CronFreshnessAssertion(BaseAssertion):
    type: Literal["cron"]

    cron: str = pydantic.Field(
        description="The cron expression to use. See https://crontab.guru/ for help."
    )
    timezone: str = pydantic.Field(
        "UTC",
        description="The timezone to use for the cron schedule. Defaults to UTC.",
    )

    def generate_freshness_assertion_schedule(self) -> FreshnessAssertionScheduleClass:
        return FreshnessAssertionScheduleClass(
            type=FreshnessAssertionScheduleTypeClass.CRON,
            cron=FreshnessCronScheduleClass(
                cron=self.cron,
                timezone=self.timezone,
            ),
        )


class FixedIntervalFreshnessAssertion(BaseAssertion):
    type: Literal["interval"]

    interval: timedelta

    def generate_freshness_assertion_schedule(self) -> FreshnessAssertionScheduleClass:
        return FreshnessAssertionScheduleClass(
            type=FreshnessAssertionScheduleTypeClass.FIXED_INTERVAL,
            fixedInterval=FixedIntervalScheduleClass(
                unit=CalendarIntervalClass.SECOND,
                multiple=int(self.interval.total_seconds()),
            ),
        )


class FreshnessAssertion(ConfigModel):
    __root__: Union[
        CronFreshnessAssertion, FixedIntervalFreshnessAssertion
    ] = pydantic.Field(discriminator="type")

    @property
    def id(self):
        return self.__root__.type

    def generate_mcp(
        self, assertion_urn: str, entity_urn: str
    ) -> List[MetadataChangeProposalWrapper]:
        aspect = AssertionInfoClass(
            type=AssertionTypeClass.FRESHNESS,
            freshnessAssertion=FreshnessAssertionInfoClass(
                entity=entity_urn,
                type=FreshnessAssertionTypeClass.DATASET_CHANGE,
                schedule=self.__root__.generate_freshness_assertion_schedule(),
            ),
            description=self.__root__.description,
        )
        return [MetadataChangeProposalWrapper(entityUrn=assertion_urn, aspect=aspect)]
