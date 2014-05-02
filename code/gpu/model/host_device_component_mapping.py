__author__ = 'mdenil'


import cpu.model.cost
import cpu.model.embedding
import cpu.model.encoding
import cpu.model.model
import cpu.model.nonlinearity
import cpu.model.pooling
import cpu.model.transfer
import cpu.model.transport

import gpu.model.cost
import gpu.model.embedding
import gpu.model.encoding
import gpu.model.model
import gpu.model.nonlinearity
import gpu.model.pooling
import gpu.model.transfer
import gpu.model.transport


__host_device_component_mapping = {
    cpu.model.cost.CrossEntropy: gpu.model.cost.CrossEntropy,

    cpu.model.embedding.WordEmbedding: gpu.model.embedding.WordEmbedding,

    cpu.model.encoding.DictionaryEncoding: gpu.model.encoding.DictionaryEncoding,

    cpu.model.model.CSM: gpu.model.model.CSM,

    cpu.model.nonlinearity.Relu: gpu.model.nonlinearity.Relu,
    cpu.model.nonlinearity.Tanh: gpu.model.nonlinearity.Tanh,

    cpu.model.pooling.KMaxPooling: gpu.model.pooling.KMaxPooling,
    cpu.model.pooling.MaxFolding: gpu.model.pooling.MaxFolding,
    cpu.model.pooling.SumFolding: gpu.model.pooling.SumFolding,

    cpu.model.transfer.Bias: gpu.model.transfer.Bias,
    cpu.model.transfer.Linear: gpu.model.transfer.Linear,
    cpu.model.transfer.SentenceConvolution: gpu.model.transfer.SentenceConvolution,
    cpu.model.transfer.Softmax: gpu.model.transfer.Softmax,

    gpu.model.transport.HostToDevice: cpu.model.transport.HostToDevice,
    gpu.model.transport.DeviceToHost: cpu.model.transport.DeviceToHost,
}

__device_host_component_mapping = dict(
    (d, h) for h, d in __host_device_component_mapping.iteritems()
)


def get_cpu_analog(gpu_class):
    return __device_host_component_mapping[gpu_class]