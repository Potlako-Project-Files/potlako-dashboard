from django.apps import apps as django_apps
from django.conf import settings
from django.core.exceptions import ObjectDoesNotExist
from edc_base.utils import get_uuid
from edc_consent.model_wrappers import ConsentModelWrapperMixin
from edc_model_wrapper import ModelWrapper

from .patient_availability_log_entry_model_wrapper import PatientAvailabilityLogEntryModelWrapper
from .subject_consent_model_wrapper import SubjectConsentModelWrapper
from .subject_locator_model_wrapper_mixin import SubjectLocatorModelWrapperMixin
from .subject_screening_model_wrapper_mixin import SubjectScreeningModelWrapperMixin

from potlako_subject.models import PatientAvailabilityLogEntry


class ClinicianCallEnrollmentModelWrapper(SubjectScreeningModelWrapperMixin,
                                          ConsentModelWrapperMixin,
                                          SubjectLocatorModelWrapperMixin,
                                          ModelWrapper):

    consent_model_wrapper_cls = SubjectConsentModelWrapper
    model = 'potlako_subject.cliniciancallenrollment'
    next_url_attrs = ['screening_identifier']
    querystring_attrs = ['screening_identifier']
    next_url_name = settings.DASHBOARD_URL_NAMES.get('screening_listboard_url')

    @property
    def log_entries(self):
        patient_availability_log = getattr(self.object, 'patientavailabilitylog')
        wrapped_entries = []
        patient_availability_log_entries = PatientAvailabilityLogEntry.objects.filter(
            patient_availability_log=patient_availability_log)
        for patient_availability_log_entry in patient_availability_log_entries:
            wrapped_entries.append(
                PatientAvailabilityLogEntryModelWrapper(patient_availability_log_entry))

        return wrapped_entries

    @property
    def can_take_call(self):
        patient_availability_log = getattr(self.object, 'patientavailabilitylog')
        can_take_call = 'No'
        log_entries = PatientAvailabilityLogEntry.objects.filter(
            patient_availability_log=patient_availability_log)
        for log_entry in log_entries:
            if log_entry.can_take_call == 'Yes':
                return True
        return can_take_call

    @property
    def log_entry(self):
        patient_availability_log = getattr(self.object, 'patientavailabilitylog')
        patient_availability_log_entry = PatientAvailabilityLogEntry(patient_availability_log=patient_availability_log)
        return PatientAvailabilityLogEntryModelWrapper(patient_availability_log_entry)

    @property
    def verbal_consent_obj(self):
        verbal_consent_cls = django_apps.get_model('potlako_subject.verbalconsent')
        try:
            return verbal_consent_cls.objects.get(
                screening_identifier=self.screening_identifier,
                version=self.consent_version)
        except ObjectDoesNotExist:
            return None

    @property
    def consent_version(self):
        return '1'

    @property
    def subject_identifier(self):
        if self.consent_model_obj:
            return self.consent_model_obj.subject_identifier
        return None

    @property
    def consent_model_obj(self):
        """Returns a consent model instance or None.
        """
        try:
            return self.subject_consent_cls.objects.get(**self.consent_options)
        except ObjectDoesNotExist:
            return None

    @property
    def subject_consent_cls(self):
        return django_apps.get_model('potlako_subject.subjectconsent')

    @property
    def create_consent_options(self):
        """Returns a dictionary of options to create a new
        unpersisted consent model instance.
        """
        options = dict(
            screening_identifier=self.screening_identifier,
            consent_identifier=get_uuid(),
            version=self.consent_version,
            first_name=self.first_name,
            last_name=self.last_name)
        return options

    @property
    def consent_options(self):
        """Returns a dictionary of options to get an existing
        consent model instance.
        """
        options = dict(
            screening_identifier=self.object.screening_identifier,
            version=self.consent_version)
        return options

    def eligible_at_enrol(self):
        return self.object.is_eligible
