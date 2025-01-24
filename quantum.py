from qiskit import QuantumCircuit
from qiskit_aer import AerSimulator
import numpy as np

PI_OVER_8 = np.pi / 8
PI_OVER_4 = np.pi / 4

class GameCircuit:
    def __init__(self, qubits):
        self.size = qubits
        self.qc = QuantumCircuit(qubits, qubits)
        self.entanglements = {}
    
    def apply_single_gate(self, gate, qubit):
        if qubit < 0 or qubit > self.size:
            print(f"[WARNING] Qubit index {qubit} out of range [0, {self.size-1}]")
            return
        gate = gate.upper()

        if gate == 'X':
            self.qc.rx(PI_OVER_8, qubit)
        elif gate == 'Y':
            self.qc.ry(PI_OVER_8, qubit)
        elif gate == 'Z':
            self.qc.rz(PI_OVER_8, qubit)
            pass
        elif gate == 'XY':
            self.qc.rz(PI_OVER_4, qubit)
            self.qc.rx(PI_OVER_8, qubit)
            self.qc.rz(-PI_OVER_4, qubit)
            pass
        elif gate == 'YZ':
            self.qc.rx(PI_OVER_4, qubit)
            self.qc.ry(PI_OVER_8, qubit)
            self.qc.rx(-PI_OVER_4, qubit)
            pass
        elif gate == 'XZ':
            self.qc.ry(PI_OVER_4, qubit)
            self.qc.rz(PI_OVER_8, qubit)
            self.qc.ry(-PI_OVER_4, qubit)
            pass
        elif gate == 'H':
            self.qc.h(qubit)
        else:
            print(f"[WARNING] Invalid gate: {gate}")

    def apply_double_gate(self, gate, control, target):
        if control < 0 or control > self.size:
            print(f"[WARNING] Control qubit index {control} out of range [0, {self.size-1}]")
            return
        if target < 0 or target > self.size:
            print(f"[WARNING] Target qubit index {target} out of range [0, {self.size-1}]")
            return
        gate = gate.upper()

        if gate == 'CX':
            self.qc.cx(control, target)
        elif gate == 'CY':
            self.qc.cy(control, target)
        elif gate == 'CZ':
            self.qc.cz(control, target)
        elif gate == 'CXY':
            self.qc.crz(PI_OVER_4, control, target)
            self.qc.crx(PI_OVER_8, control, target)
            self.qc.crz(-PI_OVER_4, control, target)
            pass
        elif gate == 'CYZ':
            self.qc.crx(PI_OVER_4, control, target)
            self.qc.cry(PI_OVER_8, control, target)
            self.qc.crx(-PI_OVER_4, control, target)
            pass
        elif gate == 'CXZ':
            self.qc.cry(PI_OVER_4, control, target)
            self.qc.crz(PI_OVER_8, control, target)
            self.qc.cry(-PI_OVER_4, control, target)
            pass
        else:
            print(f"[WARNING] Invalid gate: {gate}")
        self.entanglements[control] = target
        self.entanglements[target] = control


    def apply_swap(self, qubit1, qubit2):
        self.qc.swap(qubit1, qubit2)


    def measure_in_basis(self, qubit_index, basis):
        # Apply basis-changing gates
        if basis == 'X':
            self.qc.h(qubit_index)  # Rotate to Z basis
        elif basis == 'Y':
            self.qc.sdg(qubit_index)  # Rotate to X basis
            self.qc.h(qubit_index)  # Rotate to Z basis
        elif basis != 'Z':
            raise ValueError("Basis must be 'X', 'Y', or 'Z'")


        # Execute the circuit using the Aer simulator
        simulator = AerSimulator()

        circuit_copy = self.qc.copy()
        circuit_copy.measure(qubit_index, qubit_index)
        # Run and get counts
        result = simulator.run(circuit_copy, shots=1).result()
        counts = result.get_counts(circuit_copy)

        # Get the measurement result
        measurement_result = int(list(counts.keys())[0])  # '0' or '1'

        # Convert to +1 or -1
        observable = measurement_result * 2 - 1

        self.qc.reset(qubit_index)
        # Apply X gate to set it to |1⟩ if number is +1
        if observable == +1:
            self.qc.x(qubit_index)

        # Move the state back to the corresponding basis
        # Apply basis-changing gates
        if basis == 'X':
            self.qc.h(qubit_index)  # Rotate to X basis
        elif basis == 'Y':
            self.qc.h(qubit_index)  # Rotate to X basis
            self.qc.s(qubit_index)  # Rotate to Y basis

        return observable