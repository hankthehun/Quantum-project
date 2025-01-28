import random
from tkinter import *

import matplotlib.pyplot as plt
import networkx as nx
import numpy as np
from PIL import Image, ImageTk
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from qiskit.quantum_info import DensityMatrix
from qiskit.result import marginal_counts
from qiskit.visualization import plot_bloch_vector, plot_state_qsphere, plot_bloch_multivector
from qiskit_aer import AerSimulator

COLORS = ["gray", "blue", "red"]
LOST_BATTLE_COLORS = ["gray", "#79a0ff", "#fd8f8f"]

# Class storing all the attributes of a continent
class Continent:
	def __init__(self, name, countries=None, gate="X"):
		if countries is None:
			countries = []
		self.name = name			# Name of the continent
		self.countries = countries	# List of the country names
		self.gate = gate			# quantum gate
		self.x = 0.0
		self.y = 0.0
		self.color = "black"

	def __str__(self):
		return f"[{self.name}]:\n -> quantum gate: {self.gate}\n -> countries: {self.countries}"

	def render(self, world):
		x, y = self.x * world.size, self.y * world.size
		label = f"continent:{self.name.replace(' ', '')}"
		text = f"{self.name} ({self.gate})"
		font = ("Helvetica", 13, "bold")
		world.canvas.delete(label)
		world.canvas.create_text(x, y, fill=self.color, text=text, tags=label, font=font)


# Class storing all the attributes of a country
class Country:
	def __init__(self, name, qubits=None, continent="", x=0.0, y=0.0, owner=0):
		if qubits is None:
			qubits = []
		self.name = name			# Name of the country
		self.qubits = qubits		# Indices of the country qubits in the QC
		self.continent = continent	# Name of the continent
		self.x = x					# x position on the world map
		self.y = y					# y position on the world map
		self.owner = owner			# player owning the country
		self.lost_battle = False

	def is_owned(self, player):
		return self.owner == player

	def get_pos(self, size=1.0):
		return self.x * size, self.y * size

	def __str__(self):
		return f"[{self.name} (located in {self.continent})]:\n -> {len(self.qubits)} qubits: {self.qubits}\n -> pos: ({self.x}, {self.y})\n -> owner: {self.owner}"

	def render(self, world, selected=False):
		x, y = self.x * world.size, self.y * world.size
		size = 30 if selected else 20
		label = f"country:{self.name.replace(' ', '')}"
		world.canvas.delete(label)
		world.canvas.delete(f"{label}-title")
		if self.lost_battle:
			world.canvas.create_oval(x - size, y - size, x + size, y + size, fill=LOST_BATTLE_COLORS[self.owner], tags=label)
		else:
			world.canvas.create_oval(x - size, y - size, x + size, y + size, fill=COLORS[self.owner], tags=label)
		if selected:
			world.canvas.create_text(x, y - size - 10, text=self.name, font=("Helvetica", 10), tags=f"{label}-title")
		world.canvas.tag_bind(label, "<Button-1>", lambda e: world.select(self.name))
		world.canvas.tag_bind(label, "<Button-3>", lambda e: world.show_bloch_sphere(self))
		world.canvas.tag_bind(label, "<ButtonRelease-3>", lambda e: world.close_bloch_window())

# Class storing all the continents and country graph
class World:
	def __init__(self, country_graph=None, continents=None, size=1200):
		self.size = size
		self.country_graph = country_graph	# The graph connecting all the countries
		self.continents = continents		# A dict containing all the continents
		self.root = Tk()					# The tkinter root object
		self.root.title("Quantum Risk")
		self.root.bind("<Tab>", lambda e: self.show_circuit())
		self.canvas = Canvas(self.root, width=size, height=int(size*0.75)) # The canvas
		self.canvas.pack()
		self.selection = ""					# The name of the selected country
		self.can_select = False
		self.selection_player = 0
		self.bloch_window = None  # Store reference to the Bloch sphere window
		self.current_country = None  # Track which country's Bloch sphere is shown
		image = Image.open("background.png")
		image.thumbnail((size, int(size * 0.75)), Image.Resampling.LANCZOS)
		self.background = ImageTk.PhotoImage(image)		# The background
		self.circuit = None
		self.circuit_window = None
  
	def set_circuit(self, circuit):
		self.circuit = circuit
  
	def get_circuit(self):
		return self.circuit

	def show_circuit(self):
		if self.circuit is not None:
			self.circuit_window = Toplevel(self.root)
			self.circuit_window.title(f"Current Quantum Circuit")
			circuit_plt = self.circuit.qc.draw(output='mpl')
			canvas = FigureCanvasTkAgg(circuit_plt, master=self.circuit_window)
			canvas.draw()
			canvas.get_tk_widget().pack()

	def get_country(self, name):
		return self.country_graph.nodes[name]['country']

	def get_continent(self, name):
		return self.continents[name]

	def get_all_countries(self):
		return [node['country'] for _, node in self.country_graph.nodes(data=True)]

	def initialize_random_ownership(self):
		amount = len(self.country_graph.nodes())
		half = amount // 2
		owners = [1 for _ in range(half)] + [2 for _ in range(amount - half)]
		random.shuffle(owners)

		index = 0
		for country in self.get_all_countries():
			country.owner = owners[index]
			index = index + 1

	def estimate_bloch_vector_for_qubit(self, t):
		circ = self.get_circuit().qc
		qc = circ.copy()  # Copy the circuit
		simulator = AerSimulator()
		# Number of shots (repetitions of the experiment)
		shots = 2000
		N = shots
		# Prepare measurements for the qubit at index t
		# Z-basis (standard computational basis)
		qc_z = qc.copy()
		qc_z.measure(t, t)  # Measure qubit at index t in Z-basis
		# Run the simulation directly without `execute()`
		result_z = simulator.run(qc_z, shots=shots).result()
		counts_z = result_z.get_counts()
		# X-basis (Hadamard rotation to the X-basis)
		qc_x = qc.copy()
		qc_x.h(t)  # Apply Hadamard gate to rotate to X basis
		qc_x.measure(t, t)
		# Run the simulation directly without `execute()`
		result_x = simulator.run(qc_x, shots=shots).result()
		counts_x = result_x.get_counts()
		# Y-basis (S-gate and Hadamard for Y-basis)
		qc_y = qc.copy()
		qc_y.s(t)  # Apply S-gate for Y basis rotation
		qc_y.h(t)  # Apply Hadamard to complete the Y-basis rotation
		qc_y.measure(t, t)
		result_y = simulator.run(qc_y, shots=shots).result()
		counts_y = result_y.get_counts()
		number = self.get_qubit_amount()
		res = "0"*number
		s = number - t - 1
		respos = res[:s] + "1" + res[s+1:]
		x_avg = -(counts_x.get(respos, 0) - counts_x.get(res, 0)) / N
		y_avg = -(counts_y.get(respos, 0) - counts_y.get(res, 0)) / N
		z_avg = -(counts_z.get(respos, 0) - counts_z.get(res, 0)) / N
		# Approximate Bloch vector (x_avg, y_avg, z_avg) for the qubit at index t
		bloch_vector = np.array([x_avg, y_avg, z_avg])
		return bloch_vector

	def render_entanglement_circles(self):
		"""Render small purple dots for entangled countries"""
		self.canvas.delete("entanglement")
		if self.get_selected_country() is None:
			return

		entangled_qubits = []
		entangled_countries = []
		qubit_to_country = {}

		# Map qubits to their respective countries
		for country in self.get_all_countries():
			for qubit in country.qubits:
				qubit_to_country[qubit] = country

		for q in self.get_selected_country().qubits:
			entangled_qubits = entangled_qubits + self.circuit.get_entangled_qubits(q)

		if len(entangled_qubits) <= len(self.get_selected_country().qubits):
			return

		for q in entangled_qubits:
			c = qubit_to_country[q]
			if c not in entangled_countries:
				entangled_countries.append(c)

		# Draw entanglement circles
		for country in entangled_countries:
			size = 35 if self.get_selected_country() == country else 25
			x1, y1 = country.get_pos(self.size)
			self.canvas.create_oval(x1 - size, y1 - size, x1 + size, y1 + size, fill="purple", outline="purple", tags="entanglement")

	def array_to_integer(self, a):
		num = 0
		for i in range(len(a)):
			c = int(a[i])
			w = len(a)-i-1
			num += c*(2**w)
		return num

	def measure_partial_state(self, circuit, qubit_indices, shots = 1024):
		"""
        Measures the state vector of specified qubits in a large quantum circuit using measurements
        in the Z, X, and Y bases to extract amplitude and phase information.

        Parameters:
            circuit (QuantumCircuit): The quantum circuit to be measured.
            qubit_indices (list): The list of qubit indices to measure.
            shots (int): The number of measurement shots to perform.

        Returns:
            dict: A dictionary with binary strings as keys (representing states) and complex
                  amplitudes as values.
        """

		def measure_in_basis(circuit, qubit_indices, basis):
			"""
            Modify the circuit to measure qubits in a specific basis (X, Y, or Z).

            Parameters:
                circuit (QuantumCircuit): The circuit to modify.
                qubit_indices (list): The list of qubits to measure.
                basis (str): The basis to measure in ('X', 'Y', or 'Z').

            Returns:
                QuantumCircuit: The modified circuit with measurements in the specified basis.
            """
			new_circuit = circuit.copy()

			for qubit in qubit_indices:
				if basis == 'X':
					new_circuit.h(qubit)
				elif basis == 'Y':
					new_circuit.sdg(qubit)
					new_circuit.h(qubit)

			new_circuit.measure(qubit_indices, qubit_indices)
			return new_circuit

		# Simulate measurements in Z, X, and Y bases
		simulator = AerSimulator()
		results = {}
		for basis in ['Z', 'X', 'Y']:
			measured_circuit = measure_in_basis(circuit, qubit_indices, basis)
			result = simulator.run(measured_circuit, shots=shots).result()
			results[basis] = marginal_counts(result.get_counts(), qubit_indices)

		# Compute probabilities for Z, X, and Y bases
		probabilities = {}
		for basis, counts in results.items():
			total_counts = sum(counts.values())
			probabilities[basis] = {
				state: count / total_counts for state, count in counts.items()
			}

		# Reconstruct the state vector
		state_vector = [0 for i in range(2 ** len(qubit_indices))]
		total_states = len(state_vector)
		for i in range(total_states):
			binary_state = format(i, f'0{len(qubit_indices)}b')

			# Amplitude calculation from Z basis
			amplitude = np.sqrt(probabilities['Z'].get(binary_state, 0))

			# Phase calculation using X and Y basis measurements
			px = probabilities['X'].get(binary_state, 0)
			py = probabilities['Y'].get(binary_state, 0)
			phase = np.arctan2(py, px) if px or py else 0

			# Combine amplitude and phase
			state_vector[i] = amplitude * np.exp(1j * phase)

		return state_vector

	def visualize_bloch_spheres(self, rho):
		bloch_sphere = plot_bloch_multivector(rho)
		plt.figure(figsize=(6, 6))
		plt.imshow(bloch_sphere)
		plt.axis('off')
		plt.show()


	def show_bloch_sphere(self, country):
		if self.bloch_window is not None and self.current_country == country:
			return
		# Create new window
		# self.close_bloch_window()
		self.bloch_window = Toplevel(self.root)
		self.bloch_window.title(f"Bloch Sphere: {country.name}")
		self.current_country = country

		# Set window size and position
		self.bloch_window.geometry("600x400+100+100")

		# Create Matplotlib figure and axes
		fig = plt.figure(figsize=(4*len(country.qubits), 4))
		axes = []
		for i in range(len(country.qubits)):
			ax = fig.add_subplot(1, len(country.qubits), i + 1, projection="3d")
			axes.append(ax)

		circ = self.get_circuit().qc
		qc = circ.copy()

		for i, qubit in enumerate(country.qubits):
			entanglements = self.get_circuit().get_entangled_qubits(qubit)
			if len(entanglements) < 2:
				bloch_vector = self.estimate_bloch_vector_for_qubit(qubit)
				plot_bloch_vector(bloch_vector, ax=axes[i])
			else:
				# Calculate the entangled Bloch vector
				entanglement_indices = self.get_circuit().get_entangled_qubits(qubit)
				vector = self.measure_partial_state(self.get_circuit().qc, entanglement_indices)
				fig = plot_state_qsphere(DensityMatrix(np.outer(vector, vector)), show_state_phases = True, use_degrees = False)

		# Embed Matplotlib figure in Tkinter window
		canvas = FigureCanvasTkAgg(fig, master=self.bloch_window)
		canvas.draw()
		canvas.get_tk_widget().pack()

	def close_bloch_window(self):
		plt.close('all')
		if self.bloch_window is not None:
			self.bloch_window.destroy()
			self.bloch_window = None
			self.current_country = None

	def has_continental_bonus(self, continent, player):
		if len(continent.countries) < 2: 	# Continents with only 1 country have no bonus
			return False
		for country in continent.countries:
			if not self.get_country(country).is_owned(player):
				return False
		return True

	def get_all_continental_bonus(self, player):
		bonus = []
		for continent in self.continents.values():
			if self.has_continental_bonus(continent, player):
				bonus.append(f"C{continent.gate}")
		return bonus

	def get_all_possessions(self, player):
		return [country for country in self.get_all_countries() if country.is_owned(player)]

	def get_qubit_amount(self):
		return sum(len(country.qubits) for country in self.get_all_countries())

	def render_edge(self, a, b):
		country1 = self.get_country(a)
		country2 = self.get_country(b)
		x1, y1 = country1.x * self.size, country1.y * self.size
		x2, y2 = country2.x * self.size, country2.y * self.size
		labels = (f"edge-{country1.name}-{country2.name}", f"edge-{country2.name}-{country1.name}")
		for l in labels:
			self.canvas.delete(l)
		if abs(x1 - x2) > self.size / 2:
			self.canvas.create_line(x1, y1, 0, y1, fill="black", width=2, tags=labels)
			self.canvas.create_line(self.size, y1, x2, y2, fill="black", width=2, tags=labels)
		else:
			self.canvas.create_line(x1, y1, x2, y2, fill="black", width=2, tags=labels)

	def render_background(self):
		self.canvas.delete("background")
		self.canvas.create_image(0, 0, anchor="nw", image=self.background, tags="background")
		self.canvas.tag_lower("background")

	def render(self):
		self.render_background()
		for continent in self.continents.values():
			continent.render(self)
		for edge in self.country_graph.edges():
			self.render_edge(*edge)

		self.render_entanglement_circles()
		for country in self.get_all_countries():
			country.render(self, country.name == self.selection)

		self.canvas.tag_raise("move")
		self.root.update()

	def select(self, country):
		if not self.can_select:
			return
		if self.get_country(country).is_owned(self.selection_player) or self.selection_player == 0:
			self.selection = country
			self.render()

	def get_selected_country(self):
		if self.selection == "":
			return None
		return self.get_country(self.selection)

	def allow_selection(self, can_select, player=0, select_enemy=False):
		self.can_select = can_select
		self.selection_player = player if not select_enemy else (player % 2) + 1
		if not can_select:
			self.selection = ""

	def are_connected(self, country1, country2):
		# Get the colors of the two nodes
		c1 = self.get_country(country1)
		c2 = self.get_country(country2)
		owner1 = c1.owner
		owner2 = c2.owner

		if owner1 != owner2:
			return False

		same_owner_nodes = [c.name for c in self.get_all_possessions(owner1)]
		subgraph = self.country_graph.subgraph(same_owner_nodes)

		# Check if the two nodes are connected in this subgraph
		return nx.has_path(subgraph, country1, country2)


	def are_different_owners_and_neighbors(self, country1, country2):
		c1 = self.get_country(country1)
		c2 = self.get_country(country2)

		return c1.owner != c2.owner and self.country_graph.has_edge(country1, country2)

	def is_neighbor_with_opponent(self, country):
		owner = self.get_country(country).owner
		for c in self.country_graph.neighbors(country):
			if self.get_country(c).owner != owner:
				return True
		return False

	def is_neighbor_with_allies(self, country):
		owner = self.get_country(country).owner
		for c in self.country_graph.neighbors(country):
			if self.get_country(c).owner == owner:
				return True
		return False



	def show_temporary_message(self, text, color, time):
		self.canvas.create_rectangle(0, self.size*3//8 - 20, self.size, self.size*3//8 + 20, fill="white", tags="temporary")
		self.canvas.create_text(self.size//2, self.size*3//8, text=text, fill=color, tags="temporary", font=("Helvetica", 20))
		self.root.after(time, lambda: self.canvas.delete("temporary"))




# Load the country graph from a file
# Graph file format:
#
# Country1, 3, ContinentA, xPos, yPos
# Country2, 2, ContinentB, xPos, yPos
# Country3, 4, ContinentB, xPos, yPos
# Country4, 1, ContinentA, xPos, yPos
# Country5, 2, ContinentC, xPos, yPos
# EDGES
# Country1, Country2
# Country2, Country4
# Country4, Country3
# Country1, Country3
# CONTINENTS
# Continent1, Gate1
# Continent2, Gate2
def load_world(filename):
	country_graph = nx.Graph()
	continents_dict = {}

	with open(filename, "r") as f:  # Open Risk file
		lines = f.readlines()
		edges_section = False
		continents_section = False
		current_qubit_index = 0

		for line in lines:         # read line by line
			line = line.strip()
			if len(line) == 0:     # if line is empty, ignore
				continue
			if line == "EDGES":    # if line is "EDGES", switch to edge section
				edges_section = True
				continue
			if line == "CONTINENTS":    # if line is "CONTINENTS", switch to continents section
				continents_section = True
				continue

			if continents_section: 		# in continents section, map each continent to its corresponding quantum gate
				name, gate, color, x, y = line.split(", ")
				continent = continents_dict[name]
				continent.gate = gate
				continent.color = color
				continent.x = float(x)
				continent.y = float(y)

			elif edges_section:			# in edges section, add an edge between 2 countries in the graph
				country1, country2 = line.split(", ")
				country_graph.add_edge(country1.strip(), country2.strip())

			else:						# in countries section, add the country to the graph
				name, qubits_amount, continent, x, y, owner = line.split(", ")
				qubits = [i + current_qubit_index for i in range(int(qubits_amount))]
				current_qubit_index = current_qubit_index + int(qubits_amount)
				country_graph.add_node(name, country=Country(name, qubits, continent, float(x), float(y), int(owner)))

				if continent not in continents_dict:	# create continent if it does not exist yet
					continents_dict[continent] = Continent(continent)
				continents_dict[continent].countries.append(name)

	return World(country_graph, continents_dict)
