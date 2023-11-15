from __future__ import annotations

import datetime as dt
from abc import ABC
from dataclasses import dataclass
from decimal import Decimal

admin = ...


# Case 1: используем для авто-генерации админки


@dataclass
class Schema(ABC):
    def validate(self):
        for field, tp in self.__annotations__.items():
            value = getattr(self, field)
            if not isinstance(value, tp):
                raise ValueError(f"Wrong type of field `{field}`: {type(value)} (expected {tp})")


@dataclass
class Trade(Schema):
    date_open: dt.date
    date_close: dt.date
    price_open: Decimal
    price_close: Decimal
    extra: dict | None


# admin.add_list_view(Trade)
# admin.run_server()


# -------------------------------------

# инкапсулируем базовый html layout (header, body, footer) -
# пользователю не нужно ничего об этом знать по умолчанию


@dataclass
class Widget(ABC):
    ...


class SignalPanel(Widget):
    ...


# --------------------------------------------

BaseForm = ...
FormWidget = ...
F = ...

validator = ...
permissions_required = ...
is_admin_360 = ...

Datepicker = ...


@permissions_required(is_admin_360)
class NineboxExporter(BaseForm):
    htmx_name = "ninebox_export"

    class Widget(FormWidget):
        date_from = Datepicker()
        date_to: dt.date = F(dt.today(), validators=[lambda v: v <= dt.today()])

        @validator
        def validate_date_from(self, v: dt.date) -> True:
            first_ninebox = ...
            return first_ninebox <= v <= dt.today()
