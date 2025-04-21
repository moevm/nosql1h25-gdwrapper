from .FormattersManager import FormattersManager


formatters_manager = FormattersManager()


@formatters_manager.register_formatter()
def createdAndModifiedTimeFormatter(document):
    document["createdTime"] = document["createdTime"].replace("T", " ")[:-5]
    document["modifiedTime"] = document["modifiedTime"].replace("T", " ")[:-5]


@formatters_manager.register_formatter()
def idFormatter(document):
    document["id"] = document["_id"]


@formatters_manager.register_formatter()
def sizeFormatter(document):
    suffix = "Б"
    num = document["size"]
    for unit in ("", "К", "М", "Г", "Т", "П", "Э", "З"):
        if abs(num) < 1024.0:
            document["size"] = f"{num:3.1f} {unit}{suffix}"
            return
        num /= 1024.0
    document["size"] = f"{num:.1f} Й{suffix}"