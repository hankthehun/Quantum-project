from qiskit import QuantumCircuit
from qiskit.quantum_info import Statevector
from qiskit.visualization import plot_state_qsphere

import matplotlib.pyplot as plt
qc = QuantumCircuit(2)
qc.h(0)
qc.x(1)
 
# You can reverse the order of the qubits.
 
from qiskit.quantum_info import DensityMatrix
 
qc = QuantumCircuit(2)
qc.h(0)
qc.cx(0,1)
 
matrix = DensityMatrix(qc)
print(matrix)
plot_state_qsphere(matrix,
     show_state_phases = True, use_degrees = True)
plt.show()