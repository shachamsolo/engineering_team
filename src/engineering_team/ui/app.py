"""Gradio live build floor."""

from __future__ import annotations

import gradio as gr

from engineering_team.examples import example_rows
from engineering_team.ui.components import (
    DESIGN_PLACEHOLDER,
    HERO_HTML,
    OUTPUT_PLACEHOLDER,
    render_files,
    render_log,
    render_pipeline,
    render_status,
)
from engineering_team.ui.live import new_state, run_crew
from engineering_team.ui.styles import APP_CSS, APP_HEAD


def launch() -> None:
    """Launch a Gradio UI that collects requirements and streams crew progress."""
    idle = new_state()
    with gr.Blocks(title="Engineering Team", fill_width=True) as demo:
        with gr.Column(elem_id="build-shell"):
            gr.HTML(HERO_HTML)
            with gr.Row(equal_height=True):
                with gr.Column(scale=5, min_width=360):
                    requirements = gr.Textbox(
                        label="Product requirements",
                        placeholder="Describe the application you want the engineering team to build…",
                        lines=16,
                    )
                    gr.Examples(
                        examples=example_rows(),
                        inputs=requirements,
                        label="Example briefs",
                    )
                    start = gr.Button("Start build", variant="primary", size="lg")
                    gr.Markdown(
                        "A full run typically takes several minutes. "
                        "The sandbox is wiped at the start of every build."
                    )
                with gr.Column(scale=7, min_width=420):
                    status = gr.HTML(value=render_status(idle))
                    pipeline = gr.HTML(value=render_pipeline(idle))
                    activity = gr.HTML(value=render_log(idle), label="Live activity")
            with gr.Tabs():
                with gr.Tab("Design"):
                    design = gr.Markdown(value=DESIGN_PLACEHOLDER)
                with gr.Tab("Final write-up"):
                    output = gr.Markdown(value=OUTPUT_PLACEHOLDER)
                with gr.Tab("Sandbox files"):
                    files = gr.HTML(value=render_files([]))

        start.click(
            fn=run_crew,
            inputs=requirements,
            outputs=[status, pipeline, activity, design, output, files, start],
            concurrency_limit=1,
            show_progress="minimal",
        )

    demo.launch(css=APP_CSS, head=APP_HEAD, footer_links=["settings"])
