import networkx as nx
import random


class Continent:
	def __init__(self, name, countries=None, gate="X"):
		if countries is None:
			countries = []
		self.name = name
		self.countries = countries
		self.gate = gate
		
class Country:
	def __init__(self, name, qubits_amount=1, continent="", x=0.0, y=0.0, owner=0):
		self.name = name
		self.qubits_amount = qubits_amount
		self.continent = continent
		self.x = x
		self.y = y
		self.owner = 0


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
#
def load_countries_and_continents(filename):
	country_graph = nx.Graph()
	continents_dict = {}

	with open(filename, "r") as f:  # Open Risk file
		lines = f.readlines()
		edges_section = False
		continents_section = False

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

			if continents_section:
				continent, gate = line.split(",")
				continents_dict[continent].gate = gate

			elif edges_section:
				country1, country2 = line.split(",")
				country_graph.add_edge(country1.strip(), country2.strip())

			else:
				name, qubits_amount, continent, x, y = line.split(", ")
				country_graph.add_node(name, country=Country(name, int(qubits_amount), continent, float(x), float(y), 0))

				if continent not in continents_dict:
					continents_dict[continent] = Continent(continent)
				continents_dict[continent].countries.append(name)

	return country_graph, continents_dict



def draw_graph(country_graph, drawing_canvas, width):
	colors = ["gray", "blue", "red"]

	for edge in country_graph.edges():
		country1 = country_graph.nodes[edge[0]]['country']
		country2 = country_graph.nodes[edge[1]]['country']
		x1, y1 = country1.x * width, country1.y * width
		x2, y2 = country2.x * width, country2.y * width
		if abs(x1 - x2) > width/2:
			drawing_canvas.create_line(x1, y1, 0, y1, fill="gray", width=2)
			drawing_canvas.create_line(width, y1, x2, y2, fill="gray", width=2)
		else:
			drawing_canvas.create_line(x1, y1, x2, y2, fill="gray", width=2)

	for name, node in country_graph.nodes(data=True):
		country = node['country']
		x, y = country.x * width, country.y * width
		drawing_canvas.create_oval(x - 10, y - 10, x + 10, y + 10, fill=colors[country.owner])

		# Draw the country name above the oval
		drawing_canvas.create_text(x, y - 20, text=name, font=("Helvetica", 10, "bold"))

def setup_random_ownership(country_graph):
	amount = len(country_graph.nodes())
	half = amount//2
	owners = [1 for i in range(half)] + [2 for i in range(amount - half)]
	random.shuffle(owners)

	index = 0
	for name, node in country_graph.nodes(data=True):
		node['country'].owner = owners[index]
		index = index + 1




