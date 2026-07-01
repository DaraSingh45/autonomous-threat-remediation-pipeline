"""Generated protocol buffer code."""
from google.protobuf import descriptor as _descriptor
from google.protobuf import descriptor_pool as _descriptor_pool
from google.protobuf import runtime_version as _runtime_version
from google.protobuf import symbol_database as _symbol_database
from google.protobuf.internal import builder as _builder
_runtime_version.ValidateProtobufRuntimeVersion(
    _runtime_version.Domain.PUBLIC,
    6,
    33,
    5,
    '',
    'pipeline.proto'
)
# @@protoc_insertion_point(imports)

_sym_db = _symbol_database.Default()




DESCRIPTOR = _descriptor_pool.Default().AddSerializedFile(b'\n\x0epipeline.proto\x12\x11threatpipeline.v1\"\xaa\x02\n\x0fThreatDetection\x12\x10\n\x08\x65vent_id\x18\x01 \x01(\t\x12\x14\n\x0c\x64\x65tection_id\x18\x02 \x01(\t\x12\x1a\n\x12\x65vent_timestamp_ms\x18\x03 \x01(\x03\x12\x16\n\x0e\x64\x65tected_at_ms\x18\x04 \x01(\x03\x12\x18\n\x10\x64\x65tection_source\x18\x05 \x01(\t\x12\x11\n\trule_name\x18\x06 \x01(\t\x12\x15\n\ranomaly_score\x18\x07 \x01(\x01\x12\x10\n\x08severity\x18\x08 \x01(\t\x12\x13\n\x0b\x65ntity_type\x18\t \x01(\t\x12\x11\n\tentity_id\x18\n \x01(\t\x12\x11\n\tnamespace\x18\x0b \x01(\t\x12\x12\n\nevent_type\x18\x0c \x01(\t\x12\x16\n\x0eraw_event_json\x18\r \x01(\t\"\xd9\x01\n\x10\x44\x65\x63isionResponse\x12\x13\n\x0b\x64\x65\x63ision_id\x18\x01 \x01(\t\x12\x10\n\x08\x61pproved\x18\x02 \x01(\x08\x12\x0e\n\x06\x61\x63tion\x18\x03 \x01(\t\x12\x11\n\treasoning\x18\x04 \x01(\t\x12\x12\n\nautonomous\x18\x05 \x01(\x08\x12\x15\n\rdecided_at_ms\x18\x06 \x01(\x03\x12\x1b\n\x13remediation_success\x18\x07 \x01(\x08\x12\x1b\n\x13remediation_details\x18\x08 \x01(\t\x12\x16\n\x0eremediation_id\x18\t \x01(\t\"\xc1\x01\n\x12RemediationRequest\x12\x13\n\x0b\x64\x65\x63ision_id\x18\x01 \x01(\t\x12\x10\n\x08\x65vent_id\x18\x02 \x01(\t\x12\x14\n\x0c\x64\x65tection_id\x18\x03 \x01(\t\x12\x0e\n\x06\x61\x63tion\x18\x04 \x01(\t\x12\x13\n\x0b\x65ntity_type\x18\x05 \x01(\t\x12\x11\n\tentity_id\x18\x06 \x01(\t\x12\x11\n\tnamespace\x18\x07 \x01(\t\x12\x10\n\x08severity\x18\x08 \x01(\t\x12\x11\n\treasoning\x18\t \x01(\t\"\x96\x01\n\x13RemediationResponse\x12\x16\n\x0eremediation_id\x18\x01 \x01(\t\x12\x0f\n\x07success\x18\x02 \x01(\x08\x12\x0f\n\x07\x64\x65tails\x18\x03 \x01(\t\x12\x1e\n\x16remediation_started_ms\x18\x04 \x01(\x03\x12\x17\n\x0f\x63ompleted_at_ms\x18\x05 \x01(\x03\x12\x0c\n\x04mode\x18\x06 \x01(\t\"\x14\n\x12HealthCheckRequest\"%\n\x13HealthCheckResponse\x12\x0e\n\x06status\x18\x01 \x01(\t2\xca\x01\n\x0f\x44\x65\x63isionService\x12Y\n\x0e\x45valuateThreat\x12\".threatpipeline.v1.ThreatDetection\x1a#.threatpipeline.v1.DecisionResponse\x12\\\n\x0bHealthCheck\x12%.threatpipeline.v1.HealthCheckRequest\x1a&.threatpipeline.v1.HealthCheckResponse2\xd7\x01\n\x12RemediationService\x12\x63\n\x12\x45xecuteRemediation\x12%.threatpipeline.v1.RemediationRequest\x1a&.threatpipeline.v1.RemediationResponse\x12\\\n\x0bHealthCheck\x12%.threatpipeline.v1.HealthCheckRequest\x1a&.threatpipeline.v1.HealthCheckResponseb\x06proto3')

_globals = globals()
_builder.BuildMessageAndEnumDescriptors(DESCRIPTOR, _globals)
_builder.BuildTopDescriptorsAndMessages(DESCRIPTOR, 'pipeline_pb2', _globals)
if not _descriptor._USE_C_DESCRIPTORS:
  DESCRIPTOR._loaded_options = None
  _globals['_THREATDETECTION']._serialized_start=38
  _globals['_THREATDETECTION']._serialized_end=336
  _globals['_DECISIONRESPONSE']._serialized_start=339
  _globals['_DECISIONRESPONSE']._serialized_end=556
  _globals['_REMEDIATIONREQUEST']._serialized_start=559
  _globals['_REMEDIATIONREQUEST']._serialized_end=752
  _globals['_REMEDIATIONRESPONSE']._serialized_start=755
  _globals['_REMEDIATIONRESPONSE']._serialized_end=905
  _globals['_HEALTHCHECKREQUEST']._serialized_start=907
  _globals['_HEALTHCHECKREQUEST']._serialized_end=927
  _globals['_HEALTHCHECKRESPONSE']._serialized_start=929
  _globals['_HEALTHCHECKRESPONSE']._serialized_end=966
  _globals['_DECISIONSERVICE']._serialized_start=969
  _globals['_DECISIONSERVICE']._serialized_end=1171
  _globals['_REMEDIATIONSERVICE']._serialized_start=1174
  _globals['_REMEDIATIONSERVICE']._serialized_end=1389
# @@protoc_insertion_point(module_scope)
