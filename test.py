from qiskit import QuantumCircuit
from qiskit.quantum_info import Statevector
from qiskit.visualization import plot_state_qsphere
import matplotlib.pyplot as plt
from qiskit import QuantumCircuit, transpile, assemble
from qiskit.quantum_info import Statevector, partial_trace, DensityMatrix
from qiskit.visualization import plot_bloch_vector, plot_state_qsphere
import numpy as np

# Create a quantum circuit with 3 qubits
qc = QuantumCircuit(3)

# Apply a Hadamard gate to the first qubit
qc.h(0)
qc.cx(0, 1)
qc.cx(1, 2)
# qc.draw('mpl')
# plt.show()
matrix = DensityMatrix(qc)
print(matrix)
plot_state_qsphere(matrix,
     show_state_phases = True, use_degrees = True)
plt.show()