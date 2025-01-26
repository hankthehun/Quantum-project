from qiskit import QuantumCircuit
from qiskit_aer import AerSimulator
import numpy as np
import networkx as nx

PI_OVER_8 = np.pi / 8
PI_OVER_4 = np.pi / 4

class GameCircuit:
    def __init__(self, qubits):
        self.size = qubits
        self.qc = QuantumCircuit(qubits, qubits)
        self.entanglements = nx.Graph()
        self.entanglements.add_nodes_from(range(qubits))

    def get_entangled_qubits(self, index):
        connected_components = nx.connected_components(self.entanglements)
        for component in connected_components:
            if index in component:
                return list(component)
    
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
        self.entanglements.add_edge(control, target)


    def apply_swap(self, qubit1, qubit2):
        self.qc.swap(qubit1, qubit2)


    def measure_in_basis(self, qubit_index, basis):
        # Get all the entangled qubits and remove them from the entanglement graph
        list_to_measure = self.get_entangled_qubits(qubit_index)
        self.entanglements.remove_edges_from((u, v) for u in list_to_measure for v in list_to_measure if self.entanglements.has_edge(u, v))

        # For each qubit, apply basis-changing gates
        for qubit in list_to_measure:
            if basis == 'X':
                self.qc.h(qubit)  # Rotate to Z basis
            elif basis == 'Y':
                self.qc.sdg(qubit)  # Rotate to X basis
                self.qc.h(qubit)  # Rotate to Z basis
            elif basis != 'Z':
                raise ValueError("Basis must be 'X', 'Y', or 'Z'")

        # Create a copy of the circuit and add measurements
        circuit_copy = self.qc.copy()
        for i, qubit in enumerate(list_to_measure):
            circuit_copy.measure(qubit, i)

        # Execute the copy circuit using the Aer simulator
        simulator = AerSimulator()
        result = simulator.run(circuit_copy, shots=1).result()
        counts = result.get_counts(circuit_copy)
        return_value = 0

        # Get the measurement result
        for i, qubit in enumerate(list_to_measure):
            measurement_result = int(list(counts.keys())[0][self.size - i - 1])  # '0' or '1'

            # Convert to +1 or -1
            observable = measurement_result * 2 - 1
            if qubit == qubit_index:
                return_value = observable

            # Set the qubit to |0⟩ if observable is -1, else |1⟩
            self.qc.reset(qubit)
            if observable == +1:
                self.qc.x(qubit)

            # Move the state back to the corresponding basis
            if basis == 'X':
                self.qc.h(qubit)  # Rotate to X basis
            elif basis == 'Y':
                self.qc.h(qubit)  # Rotate to X basis
                self.qc.s(qubit)  # Rotate to Y basis

        return return_value