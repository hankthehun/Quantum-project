import networkx as nx
import random
from tkinter import *
from PIL import Image, ImageTk
import uuid

COLORS = ["gray", "blue", "red"]

# Class storing all the attributes of a continent
class Continent:
	def __init__(self, name, countries=None, gate="X"):
		if countries is None:
			countries = []
		self.name = name			# Name of the continent
		self.countries = countries	# List of the country names
		self.gate = gate			# quantum gate

	def __str__(self):
		return f"[{self.name}]:\n -> quantum gate: {self.gate}\n -> countries: {self.countries}"

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

	def is_owned(self, player):
		return self.owner == player

	def __str__(self):
		return f"[{self.name} (located in {self.continent})]:\n -> {len(self.qubits)} qubits: {self.qubits}\n -> pos: ({self.x}, {self.y})\n -> owner: {self.owner}"

	def render(self, world, selected=False):
		x, y = self.x * world.size, self.y * world.size
		size = 30 if selected else 20
		label = f"country:{self.name.replace(" ", "")}"
		world.canvas.delete(label)
		world.canvas.delete(f"{label}-title")
		world.canvas.create_oval(x - size, y - size, x + size, y + size, fill=COLORS[self.owner], tags=label)
		if selected:
			world.canvas.create_text(x, y - size - 10, text=self.name, font=("Helvetica", 10), tags=f"{label}-title")
		world.canvas.tag_bind(label, "<Button-1>", lambda e: world.select(self.name))


class Move:
	def __init__(self, gate):
		self.gate = gate
		self.selected = False

	def render(self, canvas, x, y, click_callback):
		label = f"move-{str(uuid.uuid4())}"
		size = 18 if self.selected else 15
		width = 3 if self.selected else 2
		canvas.create_rectangle(x - size, y - size, x + size, y + size, outline="black", fill="white", tags=("move", label), width=width)
		canvas.create_text(x, y, text=f"{self.gate}", font=("Helvetica", 10, "bold"), fill="black", tags=("move", label + "-text"))
		canvas.tag_bind(label, "<Button-1>", lambda e: click_callback(self))
		canvas.tag_bind(label + "-text", "<Button-1>", lambda e: click_callback(self))

# Class storing all the continents and country graph
class World:
	def __init__(self, country_graph=None, continents=None, size=1200):
		self.size = size
		self.country_graph = country_graph	# The graph connecting all the countries
		self.continents = continents		# A dict containing all the continents
		self.root = Tk()	# The tkinter root object
		self.root.title("Quantum Risk")
		self.canvas = Canvas(self.root, width=size, height=int(size*0.75)) # The canvas
		self.canvas.pack()
		self.selection = ""					# The name of the selected country
		self.can_select = False
		self.selection_player = 0

		image = Image.open("background.png")
		image.thumbnail((size, int(size * 0.75)), Image.Resampling.LANCZOS)
		self.background = ImageTk.PhotoImage(image)		# The background

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

	def get_moves(self, player):
		gates = [self.get_continent(country.continent).gate for country in self.get_all_possessions(player)]
		bonus = self.get_all_continental_bonus(player)
		return [Move(g) for g in gates + bonus]

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
		bg = self.canvas.create_image(0, 0, anchor="nw", image=self.background, tags="background")
		self.canvas.tag_lower(bg)

	def render(self):
		self.render_background()
		for edge in self.country_graph.edges():
			self.render_edge(*edge)

		for country in self.get_all_countries():
			country.render(self, country.name == self.selection)
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

	def allow_selection(self, can_select, player=0):
		self.can_select = can_select
		self.selection_player = player
		if not can_select:
			self.selection = ""




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
				continent, gate = line.split(", ")
				continents_dict[continent].gate = gate

			elif edges_section:			# in edges section, add an edge between 2 countries in the graph
				country1, country2 = line.split(", ")
				country_graph.add_edge(country1.strip(), country2.strip())

			else:						# in countries section, add the country to the graph
				name, qubits_amount, continent, x, y = line.split(", ")
				qubits = [i + current_qubit_index for i in range(int(qubits_amount))]
				current_qubit_index = current_qubit_index + int(qubits_amount)
				country_graph.add_node(name, country=Country(name, qubits, continent, float(x), float(y)))

				if continent not in continents_dict:	# create continent if it does not exist yet
					continents_dict[continent] = Continent(continent)
				continents_dict[continent].countries.append(name)

	return World(country_graph, continents_dict)
