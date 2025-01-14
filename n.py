from qiskit import QuantumCircuit
# rotations as Matrices

R_x(theta) = [[cos(theta/2), -i*sin(theta/2)],[ -i*sin(theta/2), cos(theta/2)]]
R_y(theta) = [[cos(theta/2), -sin(theta/2)],[sin(theta/2), cos(theta/2)]]
R_z(theta) = [[e^(-i*theta/2), 0],[0, e^(i*theta/2)]]

#rotations as Matrices
# Pi/8 around xy-axis
R_xy = R_z[-pi/4] * R_x[pi/8] * R_z[pi/4]
# pi/8 around yz-axis
R_yz = R_x[-pi/4] * R_y[pi/8] * R_x[pi/4]
# pi/8 around xz-axis
R_xz = R_y[-pi/4] * R_z[pi/8] * R_y[pi/4]

# add two qubit gates, first is controll qubit, second is target qubit
# controlled pi/8 rotation around x axis
CR_x = np.tensordot(np.array([[1,0],[0,1]]), R_x[pi/8], axes=0)
# controlled pi/8 rotation around y axis
CR_y = np.tensordot(np.array([[1,0],[0,1]]), R_y[pi/8], axes=0)
# controlled pi/8 rotation around z axis
CR_z = np.tensordot(np.array([[1,0],[0,1]]), R_z[pi/8], axes=0)

# controlled pi/8 rotation around xy axis
CR_xy = np.tensordot(np.array([[1,0],[0,1]]), R_xy, axes=0)
# controlled pi/8 rotation around yz axis
CR_yz = np.tensordot(np.array([[1,0],[0,1]]), R_yz, axes=0)
