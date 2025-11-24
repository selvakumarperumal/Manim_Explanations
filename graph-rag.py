import numpy as np
import mapbox_earcut

# ==============================================================================
# 🩹 CRITICAL PATCH FOR OPENGL TEXT RENDERING (MOVED TO TOP)
# ==============================================================================
# We must patch this BEFORE importing manim, otherwise manim might import 
# the original reference and ignore our wrapper.
# ==============================================================================

_real_triangulate = mapbox_earcut.triangulate_float32

def _patched_triangulate(verts, holes):
    # 1. Handle None (sometimes passed by Manim)
    if holes is None:
        holes = []
        
    # 2. Convert List to Numpy
    if isinstance(holes, list):
        holes = np.array(holes, dtype=np.uint32)
        
    # 3. Ensure existing Arrays are uint32
    elif isinstance(holes, np.ndarray) and holes.dtype != np.uint32:
        holes = holes.astype(np.uint32)
        
    return _real_triangulate(verts, holes)

mapbox_earcut.triangulate_float32 = _patched_triangulate
# ==============================================================================

# NOW we can import manim
from manim import *

# --- DRACULA THEME COLORS ---
DRACULA_BG = "#282A36"
DRACULA_FG = "#F8F8F2"
DRACULA_CYAN = "#8BE9FD"   # Entities
DRACULA_GREEN = "#50FA7B"  # Chunks / Success
DRACULA_ORANGE = "#FFB86C" # Highlights / Anchors
DRACULA_PINK = "#FF79C6"   # Semantic Relations
DRACULA_PURPLE = "#BD93F9" # LLM / Logic
DRACULA_RED = "#FF5555"    # Failures / Alerts
DRACULA_YELLOW = "#F1FA8C" # Queries
DRACULA_COMMENT = "#6272A4" # Structural Edges

class GraphRAGDraculaOpenGL(Scene):
    def construct(self):
        self.camera.background_color = DRACULA_BG
        
        # --- 1. DOCUMENT INGESTION ---
        chunks = self.scene_ingestion()
        
        # --- 2. STRUCTURAL GRAPH (CHUNKS -> NODES) ---
        nodes, s_edges = self.scene_structural_extraction(chunks)
        
        # --- 3. SEMANTIC GRAPH (NODES -> NODES) ---
        sem_edges = self.scene_semantic_extraction(nodes)
        
        # --- 4. QUERY & TRAVERSAL ---
        self.scene_query_traversal(chunks, nodes, s_edges, sem_edges)

    def scene_ingestion(self):
        # Escape '&' to '&amp;' for MarkupText
        title = MarkupText("1. Ingestion &amp; Splitting", font_size=36, color=DRACULA_PURPLE).to_edge(UP)
        self.play(Write(title))

        raw_text_str = "Alice lives in the Blue House with her dog Bob.\nBob loves eating pizza on Fridays."
        raw_box = Rectangle(height=2.5, width=8, color=DRACULA_COMMENT, fill_opacity=0.2)
        
        raw_content = MarkupText(
            raw_text_str,
            font_size=24, 
            color=DRACULA_FG
        ).move_to(raw_box)
        
        raw_group = VGroup(raw_box, raw_content)
        
        self.play(FadeIn(raw_group))
        self.wait(1)

        self.play(raw_group.animate.shift(UP * 1.5))
        
        # Chunk 1
        c1_box = RoundedRectangle(height=1.5, width=5, corner_radius=0.2, color=DRACULA_GREEN, fill_opacity=0.1)
        c1_txt = MarkupText(
            "Chunk 1:\nAlice lives in the Blue House\nwith her dog Bob.",
            font_size=18, 
            color=DRACULA_GREEN
        ).move_to(c1_box)
        chunk1 = VGroup(c1_box, c1_txt).move_to(LEFT * 3.5 + DOWN * 1)

        # Chunk 2
        c2_box = RoundedRectangle(height=1.5, width=5, corner_radius=0.2, color=DRACULA_GREEN, fill_opacity=0.1)
        c2_txt = MarkupText(
            "Chunk 2:\nBob loves eating\npizza on Fridays.",
            font_size=18, 
            color=DRACULA_GREEN
        ).move_to(c2_box)
        chunk2 = VGroup(c2_box, c2_txt).move_to(RIGHT * 3.5 + DOWN * 1)

        arrow1 = Arrow(raw_box.get_bottom(), c1_box.get_top(), color=DRACULA_COMMENT)
        arrow2 = Arrow(raw_box.get_bottom(), c2_box.get_top(), color=DRACULA_COMMENT)

        self.play(GrowArrow(arrow1), GrowArrow(arrow2))
        self.play(FadeIn(chunk1), FadeIn(chunk2))
        self.wait(1)

        self.play(
            FadeOut(raw_group), FadeOut(arrow1), FadeOut(arrow2), FadeOut(title),
            chunk1.animate.scale(0.7).to_corner(DL),
            chunk2.animate.scale(0.7).to_corner(DR)
        )
        
        return (chunk1, chunk2)

    def scene_structural_extraction(self, chunks):
        chunk1, chunk2 = chunks
        
        title = MarkupText("2. Structural Extraction (Mentions)", font_size=28, color=DRACULA_CYAN).to_edge(UP)
        subtitle = MarkupText("Connecting Text (Chunks) to Facts (Entities)", font_size=16, color=DRACULA_COMMENT).next_to(title, DOWN)
        self.play(FadeIn(title), FadeIn(subtitle))

        node_alice = self.create_node("Alice", DRACULA_CYAN).move_to(UP * 1 + LEFT * 4)
        node_house = self.create_node("Blue House", DRACULA_CYAN).move_to(UP * 2.5 + LEFT * 1)
        node_bob = self.create_node("Bob", DRACULA_ORANGE).move_to(UP * 0.5 + RIGHT * 1) 
        node_pizza = self.create_node("Pizza", DRACULA_CYAN).move_to(UP * 1 + RIGHT * 4)

        nodes_group = VGroup(node_alice, node_house, node_bob, node_pizza)
        self.play(LaggedStart(*[GrowFromCenter(n) for n in nodes_group], lag_ratio=0.2))

        edge_c1_alice = self.create_dashed_arrow(chunk1.get_top(), node_alice.get_bottom(), "mentions")
        edge_c1_house = self.create_dashed_arrow(chunk1.get_top(), node_house.get_bottom(), "") 
        edge_c1_bob = self.create_dashed_arrow(chunk1.get_right(), node_bob.get_bottom(), "mentions")
        
        edge_c2_bob = self.create_dashed_arrow(chunk2.get_left(), node_bob.get_bottom(), "mentions")
        edge_c2_pizza = self.create_dashed_arrow(chunk2.get_top(), node_pizza.get_bottom(), "mentions")

        s_edges = VGroup(edge_c1_alice, edge_c1_house, edge_c1_bob, edge_c2_bob, edge_c2_pizza)

        self.play(LaggedStart(*[Create(e) for e in s_edges], lag_ratio=0.3))
        self.wait(2)

        nodes_dict = {
            "Alice": node_alice,
            "House": node_house,
            "Bob": node_bob,
            "Pizza": node_pizza
        }

        self.play(FadeOut(title), FadeOut(subtitle))
        
        return nodes_dict, s_edges

    def scene_semantic_extraction(self, nodes):
        title = MarkupText("3. Semantic Extraction (Relationships)", font_size=36, color=DRACULA_PINK).to_edge(UP)
        self.play(FadeIn(title))

        e1 = self.create_solid_arrow(nodes["Alice"], nodes["House"], "lives_in")
        e2 = self.create_solid_arrow(nodes["Alice"], nodes["Bob"], "owns")
        e3 = self.create_solid_arrow(nodes["Bob"], nodes["Pizza"], "eats")

        sem_edges = VGroup(e1, e2, e3)
        
        self.play(Create(e1))
        self.play(Create(e2))
        self.play(Create(e3))
        self.wait(2)
        
        self.play(FadeOut(title))
        return sem_edges

    def scene_query_traversal(self, chunks, nodes, s_edges, sem_edges):
        full_graph = VGroup(chunks[0], chunks[1], *nodes.values(), s_edges, sem_edges)
        self.play(full_graph.animate.shift(DOWN * 0.5).scale(0.77))

        q_box = Rectangle(height=0.5, width=10, color=DRACULA_YELLOW, fill_opacity=0.05).to_edge(UP)
        q_text = MarkupText("User: \"What is the favorite food of the pet that lives in the Blue House?\"", font_size=18, color=DRACULA_YELLOW).move_to(q_box)
        
        self.play(Create(q_box), Write(q_text))
        self.wait(1)

        anchor_txt = MarkupText("Step 1: Identify Anchors", font_size=18, color=DRACULA_ORANGE).next_to(q_box, DOWN)
        self.play(FadeIn(anchor_txt))

        self.play(
            nodes["House"].animate.scale(1.2).set_color(DRACULA_ORANGE),
            Indicate(nodes["House"], color=DRACULA_ORANGE, scale_factor=1.2)
        )
        self.wait(0.5)
        self.play(FadeOut(anchor_txt))

        walk_txt = MarkupText("Step 2: Graph Traversal (Walking the Lines)", font_size=20, color=DRACULA_PINK).next_to(q_box, DOWN)
        self.play(FadeIn(walk_txt))

        path1 = Line(nodes["House"].get_center(), nodes["Alice"].get_center(), color=DRACULA_YELLOW, stroke_width=6)
        self.play(Create(path1), run_time=0.8)
        self.play(Indicate(nodes["Alice"], color=DRACULA_YELLOW))

        path2 = Line(nodes["Alice"].get_center(), nodes["Bob"].get_center(), color=DRACULA_YELLOW, stroke_width=6)
        self.play(Create(path2), run_time=0.8)
        self.play(Indicate(nodes["Bob"], color=DRACULA_YELLOW))

        path3 = Line(nodes["Bob"].get_center(), nodes["Pizza"].get_center(), color=DRACULA_YELLOW, stroke_width=6)
        self.play(Create(path3), run_time=0.8)
        self.play(Indicate(nodes["Pizza"], color=DRACULA_YELLOW))
        
        self.wait(1)
        self.play(FadeOut(walk_txt))

        ctx_txt = MarkupText("Step 3: Retrieve Supporting Chunks", font_size=20, color=DRACULA_GREEN).next_to(q_box, DOWN)
        self.play(FadeIn(ctx_txt))

        self.play(
            chunks[0].animate.set_stroke(DRACULA_YELLOW, width=5),
            Flash(chunks[0], color=DRACULA_YELLOW)
        )
        self.play(
            chunks[1].animate.set_stroke(DRACULA_YELLOW, width=5),
            Flash(chunks[1], color=DRACULA_YELLOW)
        )
        self.wait(1)
        self.play(FadeOut(ctx_txt))

        self.play(
            FadeOut(full_graph), 
            FadeOut(path1), FadeOut(path2), FadeOut(path3),
            q_box.animate.shift(UP * 0.5),
            q_text.animate.shift(UP * 0.5)
        )

        ans_box = RoundedRectangle(height=3.5, width=9, color=DRACULA_PURPLE, fill_opacity=0.2)
        ans_header = MarkupText("LLM Generation", font_size=28, color=DRACULA_PURPLE).next_to(ans_box, UP, buff=0.2)
        
        ans_content_str = (
            "Context: Chunk 1 (Bob lives with Alice), Chunk 2 (Bob eats Pizza)\n"
            "Graph Path: House &lt;- lives_in - Alice - owns -&gt; Bob - eats -&gt; Pizza\n\n"
            "Final Answer:\n"
            "\"The pet in the Blue House is Bob, and he loves Pizza.\""
        )
        
        ans_content = MarkupText(
            ans_content_str,
            font_size=20,
            color=DRACULA_FG
        ).move_to(ans_box)

        self.play(Create(ans_box), Write(ans_header))
        self.play(Write(ans_content))
        self.wait(3)

    # --- HELPER FUNCTIONS ---

    def create_node(self, label, color):
        circle = Circle(radius=0.5, color=color, fill_opacity=0.3)
        text = MarkupText(label, font_size=16).move_to(circle)
        text.set_color(DRACULA_FG) 
        return VGroup(circle, text).set_z_index(2)

    def create_dashed_arrow(self, start, end, label_text):
        arrow = DashedLine(start, end, color=DRACULA_COMMENT, stroke_width=2).add_tip()
        if label_text:
            label = MarkupText(label_text, font_size=12, color=DRACULA_COMMENT, slant=ITALIC).next_to(arrow, RIGHT, buff=0)
            label.move_to(arrow.get_center() + UP * 0.2)
            return VGroup(arrow, label)
        return arrow

    def create_solid_arrow(self, node_start, node_end, label_text):
        start = node_start.get_center()
        end = node_end.get_center()
        
        direction = end - start
        if np.linalg.norm(direction) == 0: 
            return VGroup()

        unit_vector = direction / np.linalg.norm(direction)
        start_point = start + unit_vector * 0.5 
        end_point = end - unit_vector * 0.5
        
        arrow = Arrow(start_point, end_point, color=DRACULA_PINK, buff=0, max_tip_length_to_length_ratio=0.1)
        
        label = MarkupText(label_text, font_size=14, color=DRACULA_PINK).move_to(arrow.get_center()).shift(UP * 0.2)
        
        bg = SurroundingRectangle(label, color=DRACULA_BG, fill_opacity=1, stroke_width=0, buff=0.05)
        
        return VGroup(arrow, bg, label).set_z_index(1)