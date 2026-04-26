import re


class RegexORM:
    @staticmethod
    def find(data_list, query=None):
        if not query:
            return data_list

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
