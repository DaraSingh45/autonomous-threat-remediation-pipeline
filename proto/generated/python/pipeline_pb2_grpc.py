"""Client and server classes corresponding to protobuf-defined services."""
import grpc
import warnings

import pipeline_pb2 as pipeline__pb2

GRPC_GENERATED_VERSION = '1.81.1'
GRPC_VERSION = grpc.__version__
_version_not_supported = False

try:
    from grpc._utilities import first_version_is_lower
    _version_not_supported = first_version_is_lower(GRPC_VERSION, GRPC_GENERATED_VERSION)
except ImportError:
    _version_not_supported = True

if _version_not_supported:
    raise RuntimeError(
        f'The grpc package installed is at version {GRPC_VERSION},'
        + ' but the generated code in pipeline_pb2_grpc.py depends on'
        + f' grpcio>={GRPC_GENERATED_VERSION}.'
        + f' Please upgrade your grpc module to grpcio>={GRPC_GENERATED_VERSION}'
        + f' or downgrade your generated code using grpcio-tools<={GRPC_VERSION}.'
    )


class DecisionServiceStub:
    """Missing associated documentation comment in .proto file."""

    def __init__(self, channel):
        """Constructor.

        Args:
            channel: A grpc.Channel.
        """
        self.EvaluateThreat = channel.unary_unary(
                '/threatpipeline.v1.DecisionService/EvaluateThreat',
                request_serializer=pipeline__pb2.ThreatDetection.SerializeToString,
                response_deserializer=pipeline__pb2.DecisionResponse.FromString,
                _registered_method=True)
        self.HealthCheck = channel.unary_unary(
                '/threatpipeline.v1.DecisionService/HealthCheck',
                request_serializer=pipeline__pb2.HealthCheckRequest.SerializeToString,
                response_deserializer=pipeline__pb2.HealthCheckResponse.FromString,
                _registered_method=True)


class DecisionServiceServicer:
    """Missing associated documentation comment in .proto file."""

    def EvaluateThreat(self, request, context):
        """Evaluate a detection against policy and, if warranted, drive the
        Remediation Agent before returning the final outcome.
        """
        context.set_code(grpc.StatusCode.UNIMPLEMENTED)
        context.set_details('Method not implemented!')
        raise NotImplementedError('Method not implemented!')

    def HealthCheck(self, request, context):
        """Missing associated documentation comment in .proto file."""
        context.set_code(grpc.StatusCode.UNIMPLEMENTED)
        context.set_details('Method not implemented!')
        raise NotImplementedError('Method not implemented!')


def add_DecisionServiceServicer_to_server(servicer, server):
    rpc_method_handlers = {
            'EvaluateThreat': grpc.unary_unary_rpc_method_handler(
                    servicer.EvaluateThreat,
                    request_deserializer=pipeline__pb2.ThreatDetection.FromString,
                    response_serializer=pipeline__pb2.DecisionResponse.SerializeToString,
            ),
            'HealthCheck': grpc.unary_unary_rpc_method_handler(
                    servicer.HealthCheck,
                    request_deserializer=pipeline__pb2.HealthCheckRequest.FromString,
                    response_serializer=pipeline__pb2.HealthCheckResponse.SerializeToString,
            ),
    }
    generic_handler = grpc.method_handlers_generic_handler(
            'threatpipeline.v1.DecisionService', rpc_method_handlers)
    server.add_generic_rpc_handlers((generic_handler,))
    server.add_registered_method_handlers('threatpipeline.v1.DecisionService', rpc_method_handlers)


 # This class is part of an EXPERIMENTAL API.
class DecisionService:
    """Missing associated documentation comment in .proto file."""

    @staticmethod
    def EvaluateThreat(request,
            target,
            options=(),
            channel_credentials=None,
            call_credentials=None,
            insecure=False,
            compression=None,
            wait_for_ready=None,
            timeout=None,
            metadata=None):
        return grpc.experimental.unary_unary(
            request,
            target,
            '/threatpipeline.v1.DecisionService/EvaluateThreat',
            pipeline__pb2.ThreatDetection.SerializeToString,
            pipeline__pb2.DecisionResponse.FromString,
            options,
            channel_credentials,
            insecure,
            call_credentials,
            compression,
            wait_for_ready,
            timeout,
            metadata,
            _registered_method=True)

    @staticmethod
    def HealthCheck(request,
            target,
            options=(),
            channel_credentials=None,
            call_credentials=None,
            insecure=False,
            compression=None,
            wait_for_ready=None,
            timeout=None,
            metadata=None):
        return grpc.experimental.unary_unary(
            request,
            target,
            '/threatpipeline.v1.DecisionService/HealthCheck',
            pipeline__pb2.HealthCheckRequest.SerializeToString,
            pipeline__pb2.HealthCheckResponse.FromString,
            options,
            channel_credentials,
            insecure,
            call_credentials,
            compression,
            wait_for_ready,
            timeout,
            metadata,
            _registered_method=True)


class RemediationServiceStub:
    """Missing associated documentation comment in .proto file."""

    def __init__(self, channel):
        """Constructor.

        Args:
            channel: A grpc.Channel.
        """
        self.ExecuteRemediation = channel.unary_unary(
                '/threatpipeline.v1.RemediationService/ExecuteRemediation',
                request_serializer=pipeline__pb2.RemediationRequest.SerializeToString,
                response_deserializer=pipeline__pb2.RemediationResponse.FromString,
                _registered_method=True)
        self.HealthCheck = channel.unary_unary(
                '/threatpipeline.v1.RemediationService/HealthCheck',
                request_serializer=pipeline__pb2.HealthCheckRequest.SerializeToString,
                response_deserializer=pipeline__pb2.HealthCheckResponse.FromString,
                _registered_method=True)


class RemediationServiceServicer:
    """Missing associated documentation comment in .proto file."""

    def ExecuteRemediation(self, request, context):
        """Missing associated documentation comment in .proto file."""
        context.set_code(grpc.StatusCode.UNIMPLEMENTED)
        context.set_details('Method not implemented!')
        raise NotImplementedError('Method not implemented!')

    def HealthCheck(self, request, context):
        """Missing associated documentation comment in .proto file."""
        context.set_code(grpc.StatusCode.UNIMPLEMENTED)
        context.set_details('Method not implemented!')
        raise NotImplementedError('Method not implemented!')


def add_RemediationServiceServicer_to_server(servicer, server):
    rpc_method_handlers = {
            'ExecuteRemediation': grpc.unary_unary_rpc_method_handler(
                    servicer.ExecuteRemediation,
                    request_deserializer=pipeline__pb2.RemediationRequest.FromString,
                    response_serializer=pipeline__pb2.RemediationResponse.SerializeToString,
            ),
            'HealthCheck': grpc.unary_unary_rpc_method_handler(
                    servicer.HealthCheck,
                    request_deserializer=pipeline__pb2.HealthCheckRequest.FromString,
                    response_serializer=pipeline__pb2.HealthCheckResponse.SerializeToString,
            ),
    }
    generic_handler = grpc.method_handlers_generic_handler(
            'threatpipeline.v1.RemediationService', rpc_method_handlers)
    server.add_generic_rpc_handlers((generic_handler,))
    server.add_registered_method_handlers('threatpipeline.v1.RemediationService', rpc_method_handlers)


 # This class is part of an EXPERIMENTAL API.
class RemediationService:
    """Missing associated documentation comment in .proto file."""

    @staticmethod
    def ExecuteRemediation(request,
            target,
            options=(),
            channel_credentials=None,
            call_credentials=None,
            insecure=False,
            compression=None,
            wait_for_ready=None,
            timeout=None,
            metadata=None):
        return grpc.experimental.unary_unary(
            request,
            target,
            '/threatpipeline.v1.RemediationService/ExecuteRemediation',
            pipeline__pb2.RemediationRequest.SerializeToString,
            pipeline__pb2.RemediationResponse.FromString,
            options,
            channel_credentials,
            insecure,
            call_credentials,
            compression,
            wait_for_ready,
            timeout,
            metadata,
            _registered_method=True)

    @staticmethod
    def HealthCheck(request,
            target,
            options=(),
            channel_credentials=None,
            call_credentials=None,
            insecure=False,
            compression=None,
            wait_for_ready=None,
            timeout=None,
            metadata=None):
        return grpc.experimental.unary_unary(
            request,
            target,
            '/threatpipeline.v1.RemediationService/HealthCheck',
            pipeline__pb2.HealthCheckRequest.SerializeToString,
            pipeline__pb2.HealthCheckResponse.FromString,
            options,
            channel_credentials,
            insecure,
            call_credentials,
            compression,
            wait_for_ready,
            timeout,
            metadata,
            _registered_method=True)
