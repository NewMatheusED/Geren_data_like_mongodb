import re


class RegexORM:
    @staticmethod
    def find(data_list, query=None):
        if not query:
            return data_list

        for key, value in query.items():
            try:
                re.compile(str(value))
            except re.error as e:
                raise ValueError(
                    f"Padrão regex inválido no campo '{key}': '{value}' → {e}"
                )

        result = []
        for item in data_list:
            match = True
            for key, value in query.items():
                if key not in item:
                    match = False
                    break

                if not re.search(str(value), str(item[key]), re.IGNORECASE):
                    match = False
                    break

            if match:
                result.append(item)

        return result
