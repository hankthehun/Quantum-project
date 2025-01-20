import uuid

class PlacingMove:
	def __init__(self, gate):
		self.gate = gate
		self.selected = False
		self.country1 = ""
		self.country2 = ""
		self.qubit1 = 0
		self.qubit2 = 0

	def render(self, world, x, y, click_callback):
		label = f"move-{str(uuid.uuid4())}"
		size = 18 if self.selected else 15
		width = 3 if self.selected else 2
		color = "orange" if self.is_double_gate() else "black"
		world.canvas.create_rectangle(x - size, y - size, x + size, y + size, outline=color, fill="white", tags=("move", label), width=width)
		world.canvas.create_text(x, y, text=f"{self.gate}", font=("Helvetica", 10, "bold"), fill=color, tags=("move", label + "-text"))
		world.canvas.tag_bind(label, "<Button-1>", lambda e: click_callback(self))
		world.canvas.tag_bind(label + "-text", "<Button-1>", lambda e: click_callback(self))
		if self.country1 != "":
			x1, y1 = world.get_country(self.country1).get_pos(world.size)
			if world.selection not in ["", self.country1]:
				x2, y2 = world.get_selected_country().get_pos(world.size)
				world.canvas.create_oval(x2 - 5, y2 - 5, x2 + 5, y2 + 5, fill="green", tags="move")
				world.canvas.create_line(x2, y2, x1, y1, fill="green", tags="move", width=5, arrow="last", arrowshape=(20, 20, 10))
			else:
				world.canvas.create_oval(x1 - 5, y1 - 5, x1 + 5, y1 + 5, fill="green", tags="move")

	def is_double_gate(self):
		return self.gate in ["CX", "CY", "CZ", "CXY", "CYZ", "CXZ"]

	def select_country(self, country):
		if self.country1 == "":
			self.country1 = country
			return not self.is_double_gate()

		elif self.country1 == country:
			return False
		else:
			self.country2 = country
			return True

	def set_selected(self, selected):
		if not selected:
			self.country1 = ""
		self.selected = selected

	def __str__(self):
		if self.is_double_gate():
			return f"Move [{self.gate}]: {self.country2}({self.qubit2}) -> {self.country1}({self.qubit1})"
		return f"Move [{self.gate}]: {self.country1}({self.qubit1})"


def get_player_placing_moves(world, player):
	gates = [world.get_continent(country.continent).gate for country in world.get_all_possessions(player)]
	bonus = world.get_all_continental_bonus(player)
	return [PlacingMove(g) for g in gates + bonus]

def get_move_render_positions(x, y, amount):
	positions = []
	for index in range(amount):
		column = index//5
		row = index%5
		positions.append((x + row*40, y + column*40))
	return positions

def get_player_attacking_moves():
	moves = [None, None, None]

	moveX = AttackingMove()
	moveY = AttackingMove()
	moveZ = AttackingMove()

	moveX.basis = "X"
	moveY.basis = "Y"
	moveZ.basis = "Z"

	moves[0] = moveX
	moves[1] = moveY
	moves[2] = moveZ

	return moves

class AttackingMove:
	def __init__(self):
		self.basis = ""
		self.selected = False
		self.country1 = ""
		self.country2 = ""
		self.qubit1 = 0
		self.qubit2 = 0


	def select_country(self, world, country):
		if self.country1 == "":
			if world.get_country(country).lost_battle:
				world.show_temporary_message("This country already lost a battle,"
											 " select a new country", "red", 2000)
				return False
			if world.is_neighbor_with_opponent(country):
				self.country1 = country
				return True
			else:
				world.show_temporary_message("Select a country neighbor with the opponent", "red", 2000)
				return False
		if world.are_different_owners_and_connected(self.country1, country):
			self.country2 = country
			return True
		world.show_temporary_message("Select a connected enemy country", "red", 2000)


	def render_selection(self, world):
		world.canvas.delete("selection")
		world.canvas.delete("basis")
		if self.country1 != "":
			x, y = world.get_country(self.country1).get_pos()
			x = x * world.size
			y = y * world.size
			world.canvas.create_rectangle(x - 5, y - 5, x + 5, y + 5, fill="green", tags="selection")


	def render_measurement_basis(self, world, x, y, click_callback):
		label = f"basis-{str(uuid.uuid4())}"
		size = 18 if self.selected else 15
		width = 3 if self.selected else 2

		world.canvas.create_rectangle(x - size, y - size, x + size, y + size, outline="black", fill="white",
									  tags=("basis", label), width=width)
		world.canvas.create_text(x, y, text=f"{self.basis}", font=("Helvetica", 18, "bold"), fill="black",
								 tags=("basis", label + "-text"))
		world.canvas.tag_bind(label, "<Button-1>", lambda e: click_callback(self))
		world.canvas.tag_bind(label + "-text", "<Button-1>", lambda e: click_callback(self))


	def set_selected(self, selected):
		self.selected = selected


	def __str__(self, ):
		return f"Attack ({self.basis} basis): {self.country1}({self.qubit1}) --> {self.country2}({self.qubit2})"

class TroopSwap:
	def __init__(self):
		self.country1 = ""
		self.country2 = ""
		self.qubit1 = 0
		self.qubit2 = 0

	def select_country(self, world, country):
		if self.country1 == "":
			if world.is_neighbor_with_allies(country):
				self.country1 = country
			else:
				world.show_temporary_message("Select a country with allied neighbors", "red", 2000)
			return False
		if world.are_connected(self.country1, country):
			self.country2 = country
			return True
		world.show_temporary_message("Select a connected country", "red", 2000)
		return False

	def render(self, world):
		world.canvas.delete("swap")
		if self.country1 != "":
			x1, y1 = world.get_country(self.country1).get_pos(world.size)
			if world.selection not in ["", self.country1]:
				x2, y2 = world.get_selected_country().get_pos(world.size)
				color = "green" if world.are_connected(self.country1, world.selection) else "red"
				world.canvas.create_line(x2, y2, x1, y1, fill=color, tags="swap", width=5, arrow="both", arrowshape=(20, 20, 10))
			else:
				world.canvas.create_oval(x1 - 5, y1 - 5, x1 + 5, y1 + 5, fill="green", tags="swap")

	def __str__(self):
		return f"Swap: {self.country2}({self.qubit2}) <-> {self.country1}({self.qubit1})"
