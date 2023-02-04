import logging
from pathlib import Path

from py_executable_checklist.workflow import WorkflowBase, run_command, run_workflow


class ConvertImageToText(WorkflowBase):
    """
    Convert image to text using tesseract
    """

    image_file_path: Path

    def execute(self) -> dict:
        image_name = self.image_file_path.stem
        text_path = self.image_file_path.parent / f"{image_name}"
        tesseract_command = f"tesseract {self.image_file_path} {text_path} --oem 1 -l eng"
        run_command(tesseract_command)
        logging.info(f"Converted {self.image_file_path} to {text_path}")
        converted_text = text_path.with_suffix(".txt").read_text()
        text_path.with_suffix(".txt").unlink()
        return {"converted_text": converted_text}


def workflow():
    return [
        ConvertImageToText,
    ]


def main(photo_file_path):
    context = {"image_file_path": Path(photo_file_path)}
    run_workflow(context, workflow())
    return context["converted_text"]
