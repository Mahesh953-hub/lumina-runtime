from __future__ import annotations

from pydantic import BaseModel, Field, model_validator


class CreateRequest(BaseModel):
    prompt: str = Field(min_length=1, max_length=4000)
    width: int = Field(default=512, ge=16, le=2048)
    height: int = Field(default=512, ge=16, le=2048)
    provider: str = Field(default="canvas", pattern="^(canvas|openai-compatible)$")


class EditRequest(BaseModel):
    image_base64: str = Field(min_length=1, max_length=20_000_000)
    operation: str
    params: dict = Field(default_factory=dict)

    @model_validator(mode="after")
    def validate_operation(self):
        allowed = {
            "draw_rectangle",
            "draw_ellipse",
            "draw_text",
            "blur",
            "sharpen",
            "brighten",
            "contrast",
        }
        if self.operation not in allowed:
            raise ValueError(f"unsupported operation: {self.operation}")
        return self


class ReviseRequest(BaseModel):
    image_base64: str = Field(min_length=1, max_length=20_000_000)
    instruction: str = Field(min_length=1, max_length=2000)
    max_iterations: int = Field(default=1, ge=1, le=3)
