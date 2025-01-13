import tkinter as tk
from qiskit import *
from graph import *

if __name__ == "__main__":
	root = tk.Tk()
	root.title("Risk World Map")
	canvas = tk.Canvas(root, width=1200, height=900)
	canvas.pack()
	graph, continents = load_countries_and_continents("risk_graph.txt")
	setup_random_ownership(graph)
	draw_graph(graph, canvas, 1200)
	root.mainloop()