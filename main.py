import tkinter as tk
from graph import *

if __name__ == "__main__":
	world = load_world("risk_graph.txt")
	world.initialize_random_ownership()
	world.render()

	print("Debug")
	print(world.get_moves(1))