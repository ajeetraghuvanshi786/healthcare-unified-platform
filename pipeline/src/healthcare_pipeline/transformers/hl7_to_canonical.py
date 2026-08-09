from __future__ import annotations

from healthcare_pipeline.canonical import (
    Address,
    AdministrativeGender,
    Allergy,
    CanonicalClinicalMessage,
    Coding,
    ContactPoint,
    ContactPointSystem,
    Coverage,
    Diagnosis,
    Encounter,
    EncounterClass,
    HumanName,
    Identifier,
    Location,
    MedicationAdministration,
    MedicationOrder,
    MedicationRoute,
    Observation,
    ObservationOrder,
    Patient,
    Period,
    Provider,
    Quantity,
)
from healthcare_pipeline.parsers.hl7 import AdministrativeSex, PatientClass
from healthcare_pipeline.parsers.hl7.clinical.allergy import Allergy as HL7Allergy
from healthcare_pipeline.parsers.hl7.clinical.diagnosis import Diagnosis as HL7Diagnosis
from healthcare_pipeline.parsers.hl7.datatypes.coded_value import CodedValue
from healthcare_pipeline.parsers.hl7.datatypes.order_identifier import OrderIdentifier
from healthcare_pipeline.parsers.hl7.demographics.patient import Patient as HL7Patient
from healthcare_pipeline.parsers.hl7.demographics.patient_address import PatientAddress
from healthcare_pipeline.parsers.hl7.demographics.patient_identifier import PatientIdentifier
from healthcare_pipeline.parsers.hl7.demographics.patient_name import PatientName
from healthcare_pipeline.parsers.hl7.demographics.patient_phone import PatientPhone
from healthcare_pipeline.parsers.hl7.encounters.patient_encounter import PatientEncounter
from healthcare_pipeline.parsers.hl7.encounters.patient_location import PatientLocation
from healthcare_pipeline.parsers.hl7.encounters.provider import Provider as HL7Provider
from healthcare_pipeline.parsers.hl7.financial.insurance_coverage import InsuranceCoverage
from healthcare_pipeline.parsers.hl7.orders.observation_result import ObservationResult
from healthcare_pipeline.parsers.hl7.pharmacy.medication_administration import (
    MedicationAdministration as HL7MedicationAdministration,
)
from healthcare_pipeline.parsers.hl7.pharmacy.pharmacy_route import PharmacyRoute
from healthcare_pipeline.parsers.hl7.workflow.clinical_message import HL7ClinicalMessage
from healthcare_pipeline.parsers.hl7.workflow.medication_order_group import MedicationOrderGroup
from healthcare_pipeline.parsers.hl7.workflow.observation_order_group import ObservationOrderGroup


class HL7ToCanonicalTransformer:
    """Anti-corruption layer translating HL7 semantic objects into canonical objects."""

    def transform(self, message: HL7ClinicalMessage) -> CanonicalClinicalMessage:
        if not isinstance(message, HL7ClinicalMessage):
            raise TypeError("message must be an HL7ClinicalMessage")

        medication_orders: list[MedicationOrder] = []
        medication_administrations: list[MedicationAdministration] = []
        for group in message.medication_orders:
            if group.encoded_order is not None:
                medication_orders.append(self._medication_order(group))
            medication_administrations.extend(self._medication_administrations(group))

        return CanonicalClinicalMessage(
            source_format="hl7_v2",
            source_message_id=message.message_control_id,
            source_event_code=message.event_code,
            patient=self._patient(message.patient) if message.patient is not None else None,
            encounter=(
                self._encounter(message.encounter) if message.encounter is not None else None
            ),
            coverages=tuple(self._coverage(value) for value in message.insurance_coverages),
            diagnoses=tuple(self._diagnosis(value) for value in message.diagnoses),
            allergies=tuple(self._allergy(value) for value in message.allergies),
            observation_orders=tuple(
                self._observation_order(value) for value in message.observation_orders
            ),
            medication_orders=tuple(medication_orders),
            medication_administrations=tuple(medication_administrations),
        )

    @staticmethod
    def _coding(value: CodedValue | None) -> Coding | None:
        if value is None:
            return None
        return Coding(code=value.identifier, display=value.text, system=value.coding_system)

    @staticmethod
    def _identifier(value: PatientIdentifier) -> Identifier:
        return Identifier(
            value=value.value,
            system=value.assigning_authority,
            type_code=value.identifier_type,
            assigner=value.assigning_facility,
        )

    @staticmethod
    def _order_identifier(value: OrderIdentifier | None) -> Identifier | None:
        if value is None:
            return None
        return Identifier(
            value=value.entity_identifier,
            system=value.namespace_id,
            type_code="order",
            assigner=value.universal_id,
        )

    @staticmethod
    def _name(value: PatientName) -> HumanName:
        given = tuple(
            item for item in (value.given_name, value.middle_name) if item is not None
        )
        prefix = (value.prefix,) if value.prefix is not None else ()
        suffix = tuple(item for item in (value.suffix, value.degree) if item is not None)
        return HumanName(
            family=value.family_name,
            given=given,
            prefix=prefix,
            suffix=suffix,
            use=value.name_type,
        )

    @staticmethod
    def _address(value: PatientAddress) -> Address:
        lines = tuple(
            item for item in (value.street_address, value.other_designation) if item is not None
        )
        return Address(
            lines=lines,
            city=value.city,
            state=value.state_or_province,
            postal_code=value.postal_code,
            country=value.country,
            district=value.county,
            use=value.address_type,
        )

    @staticmethod
    def _contact(value: PatientPhone) -> tuple[ContactPoint, ...]:
        contacts: list[ContactPoint] = []
        if value.email is not None:
            contacts.append(
                ContactPoint(
                    system=ContactPointSystem.EMAIL,
                    value=value.email,
                    use=value.use_code,
                )
            )
        number = value.number or value.local_number
        if number is not None:
            equipment = (value.equipment_type or "").upper()
            system = ContactPointSystem.PHONE
            if equipment in {"FX", "FAX"}:
                system = ContactPointSystem.FAX
            elif equipment in {"BP", "PAGER"}:
                system = ContactPointSystem.PAGER
            contacts.append(ContactPoint(system=system, value=number, use=value.use_code))
        return tuple(contacts)

    @staticmethod
    def _provider(value: HL7Provider) -> Provider:
        identifiers: tuple[Identifier, ...] = ()
        if value.identifier is not None:
            identifiers = (
                Identifier(
                    value=value.identifier,
                    system=value.assigning_authority,
                    type_code=value.identifier_type,
                ),
            )
        names: tuple[HumanName, ...] = ()
        if value.family_name is not None or value.given_name is not None:
            names = (
                HumanName(
                    family=value.family_name,
                    given=tuple(
                        item
                        for item in (value.given_name, value.middle_name)
                        if item is not None
                    ),
                    prefix=(value.prefix,) if value.prefix is not None else (),
                    suffix=(value.suffix,) if value.suffix is not None else (),
                    use=value.name_type,
                ),
            )
        qualifications = (
            (value.professional_degree,) if value.professional_degree is not None else ()
        )
        return Provider(
            identifiers=identifiers,
            names=names,
            qualifications=qualifications,
        )

    @staticmethod
    def _location(value: PatientLocation) -> Location:
        return Location(
            facility=value.facility,
            building=value.building,
            floor=value.floor,
            point_of_care=value.point_of_care,
            room=value.room,
            bed=value.bed,
            description=value.description,
        )

    def _patient(self, value: HL7Patient) -> Patient:
        account_identifiers: tuple[Identifier, ...] = ()
        if value.patient_account_number is not None:
            account_identifiers = (self._identifier(value.patient_account_number),)
        telecom = tuple(
            contact for phone in value.phones for contact in self._contact(phone)
        )
        gender_mapping = {
            AdministrativeSex.MALE: AdministrativeGender.MALE,
            AdministrativeSex.FEMALE: AdministrativeGender.FEMALE,
            AdministrativeSex.OTHER: AdministrativeGender.OTHER,
        }
        return Patient(
            identifiers=tuple(self._identifier(item) for item in value.identifiers),
            names=tuple(self._name(item) for item in value.names),
            birth_date=value.birth_date,
            administrative_gender=gender_mapping.get(
                value.administrative_sex,
                AdministrativeGender.UNKNOWN,
            ),
            addresses=tuple(self._address(item) for item in value.addresses),
            telecom=telecom,
            account_identifiers=account_identifiers,
        )

    def _encounter(self, value: PatientEncounter) -> Encounter:
        class_mapping = {
            PatientClass.INPATIENT: EncounterClass.INPATIENT,
            PatientClass.OUTPATIENT: EncounterClass.OUTPATIENT,
            PatientClass.EMERGENCY: EncounterClass.EMERGENCY,
            PatientClass.PREADMIT: EncounterClass.PREADMIT,
            PatientClass.RECURRING: EncounterClass.RECURRING,
            PatientClass.OBSTETRICS: EncounterClass.OBSTETRICS,
        }
        identifiers: tuple[Identifier, ...] = ()
        if value.visit_number is not None:
            identifiers = (self._identifier(value.visit_number),)
        locations = tuple(
            self._location(item)
            for item in (value.assigned_location, value.temporary_location, value.prior_location)
            if item is not None
        )
        period: Period | None = None
        if value.admit_datetime is not None or value.discharge_datetime is not None:
            period = Period(start=value.admit_datetime, end=value.discharge_datetime)
        return Encounter(
            encounter_class=class_mapping.get(value.patient_class, EncounterClass.UNKNOWN),
            identifiers=identifiers,
            period=period,
            locations=locations,
            attending_providers=(
                (self._provider(value.attending_provider),)
                if value.attending_provider is not None
                else ()
            ),
            referring_providers=(
                (self._provider(value.referring_provider),)
                if value.referring_provider is not None
                else ()
            ),
            consulting_providers=tuple(
                self._provider(item) for item in value.consulting_providers
            ),
            admitting_providers=(
                (self._provider(value.admitting_provider),)
                if value.admitting_provider is not None
                else ()
            ),
            service_type=value.hospital_service,
            admission_type=value.admission_type,
            discharge_disposition=value.discharge_disposition,
        )

    def _coverage(self, value: InsuranceCoverage) -> Coverage:
        policy_identifiers: tuple[Identifier, ...] = ()
        if value.policy_number is not None:
            policy_identifiers = (Identifier(value=value.policy_number, type_code="policy"),)
        return Coverage(
            policy_identifiers=policy_identifiers,
            plan=self._coding(value.plan_identifier),
            payer_identifiers=tuple(
                self._identifier(item) for item in value.company_identifiers
            ),
            payer_name=value.company_name,
            payer_addresses=tuple(self._address(item) for item in value.company_addresses),
            payer_telecom=tuple(
                contact
                for phone in value.contact_phones
                for contact in self._contact(phone)
            ),
            group_number=value.group_number,
            group_name=value.group_name,
            effective_date=value.effective_date,
            expiration_date=value.expiration_date,
            subscriber_names=tuple(self._name(item) for item in value.insured_names),
            subscriber_identifiers=tuple(
                self._identifier(item) for item in value.insured_identifiers
            ),
            relationship=self._coding(value.insured_relationship),
        )

    def _diagnosis(self, value: HL7Diagnosis) -> Diagnosis:
        code = self._coding(value.code)
        assert code is not None
        return Diagnosis(
            code=code,
            recorded_datetime=value.diagnosis_datetime,
            diagnosis_type=value.diagnosis_type,
            priority=value.priority,
            diagnosing_providers=tuple(
                self._provider(item) for item in value.diagnosing_providers
            ),
        )

    def _allergy(self, value: HL7Allergy) -> Allergy:
        allergen = self._coding(value.allergen)
        assert allergen is not None
        return Allergy(
            allergen=allergen,
            category=self._coding(value.allergy_type),
            severity=self._coding(value.severity),
            reactions=value.reactions,
            identified_date=value.identification_date,
        )

    def _observation(self, value: ObservationResult) -> Observation:
        code = self._coding(value.observation_identifier)
        assert code is not None
        return Observation(
            code=code,
            values=value.values,
            status=value.result_status,
            value_type=value.value_type,
            units=self._coding(value.units),
            reference_range=value.reference_range,
            abnormal_flags=value.abnormal_flags,
            effective_datetime=value.observation_datetime,
            performers=tuple(self._provider(item) for item in value.responsible_observers),
            methods=tuple(
                coding
                for item in value.observation_method
                if (coding := self._coding(item)) is not None
            ),
        )

    def _observation_order(self, value: ObservationOrderGroup) -> ObservationOrder:
        request = value.request
        service = self._coding(request.universal_service_identifier)
        assert service is not None
        identifiers = tuple(
            item
            for candidate in (
                self._order_identifier(request.placer_order_number),
                self._order_identifier(request.filler_order_number),
            )
            if (item := candidate) is not None
        )
        return ObservationOrder(
            service=service,
            identifiers=identifiers,
            status=request.result_status,
            requested_datetime=request.requested_datetime,
            observation_datetime=request.observation_datetime,
            ordering_providers=tuple(
                self._provider(item) for item in request.ordering_providers
            ),
            reasons=tuple(
                coding
                for item in request.reasons_for_study
                if (coding := self._coding(item)) is not None
            ),
            results=tuple(self._observation(item) for item in value.results),
        )

    def _route(self, value: PharmacyRoute) -> MedicationRoute:
        route = self._coding(value.route)
        assert route is not None
        return MedicationRoute(
            route=route,
            site=self._coding(value.administration_site),
            method=self._coding(value.administration_method),
            device=self._coding(value.administration_device),
        )

    def _medication_order(self, group: MedicationOrderGroup) -> MedicationOrder:
        encoded = group.encoded_order
        assert encoded is not None
        medication = self._coding(encoded.give_code)
        assert medication is not None
        dose_minimum: Quantity | None = None
        if encoded.give_amount_minimum is not None:
            dose_minimum = Quantity(
                encoded.give_amount_minimum,
                self._coding(encoded.give_units),
            )
        dose_maximum: Quantity | None = None
        if encoded.give_amount_maximum is not None:
            dose_maximum = Quantity(
                encoded.give_amount_maximum,
                self._coding(encoded.give_units),
            )
        dispense_quantity: Quantity | None = None
        if encoded.dispense_amount is not None:
            dispense_quantity = Quantity(
                encoded.dispense_amount,
                self._coding(encoded.dispense_units),
            )
        identifiers: tuple[Identifier, ...] = ()
        if group.common_order is not None:
            identifiers = tuple(
                item
                for candidate in (
                    self._order_identifier(group.common_order.placer_order_number),
                    self._order_identifier(group.common_order.filler_order_number),
                )
                if (item := candidate) is not None
            )
        return MedicationOrder(
            medication=medication,
            identifiers=identifiers,
            dose_minimum=dose_minimum,
            dose_maximum=dose_maximum,
            dispense_quantity=dispense_quantity,
            number_of_refills=encoded.number_of_refills,
            ordering_providers=tuple(
                self._provider(item) for item in encoded.ordering_providers
            ),
            routes=tuple(self._route(item) for item in group.routes),
            status=(group.common_order.order_status if group.common_order is not None else None),
            instructions=tuple(
                coding
                for item in encoded.provider_instructions
                if (coding := self._coding(item)) is not None
            ),
            strength=encoded.give_strength,
            strength_unit=self._coding(encoded.give_strength_units),
        )

    def _medication_administrations(
        self,
        group: MedicationOrderGroup,
    ) -> tuple[MedicationAdministration, ...]:
        routes = tuple(self._route(item) for item in group.routes)
        return tuple(
            self._medication_administration(item, routes) for item in group.administrations
        )

    def _medication_administration(
        self,
        value: HL7MedicationAdministration,
        routes: tuple[MedicationRoute, ...],
    ) -> MedicationAdministration:
        medication = self._coding(value.administered_code)
        assert medication is not None
        return MedicationAdministration(
            medication=medication,
            amount=Quantity(value.administered_amount, self._coding(value.administered_units)),
            start_datetime=value.start_datetime,
            end_datetime=value.end_datetime,
            routes=routes,
            performers=tuple(
                self._provider(item) for item in value.administering_providers
            ),
            location=(
                self._location(value.administered_at_location)
                if value.administered_at_location is not None
                else None
            ),
            lot_number=value.lot_number,
            expiration_date=value.expiration_date,
            manufacturer=self._coding(value.manufacturer),
            refusal_reason=self._coding(value.refusal_reason),
            indication=self._coding(value.indication),
            status=value.completion_status,
        )
