import tkinter as tk
from graph import *

if __name__ == "__main__":
	root = tk.Tk()
	root.title("Risk World Map")
	canvas = tk.Canvas(root, width=1200, height=900)
	canvas.pack()
	world = load_world("risk_graph.txt")
	world.initialize_random_ownership()

	print("Debug")
	print(world.get_moves(1))
	draw_world(world, canvas, 1200)
	root.mainloop()