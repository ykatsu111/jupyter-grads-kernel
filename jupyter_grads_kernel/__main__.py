from ipykernel.kernelapp import IPKernelApp
from .kernel import GradsKernel

IPKernelApp.launch_instance(kernel_class=GradsKernel)
