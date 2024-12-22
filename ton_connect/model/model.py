import pydantic


class BaseModel(pydantic.BaseModel):
    model_config = pydantic.ConfigDict(
        populate_by_name=True,
        json_encoders={
            bytes: lambda v: v.hex(),
        },
    )
