import pandas as pd
from decouple import config
from collections import defaultdict
import seaborn as sns
import matplotlib.pyplot as plt


class UtilsEDA:
    @staticmethod
    def create_datadict(
        dataframe: pd.DataFrame, group_by: str, return_data: str
    ) -> dict:
        data = dict()
        for index, code in enumerate(dataframe["codCBO"].unique()):
            tmp_ = dict(
                round(
                    dataframe.loc[dataframe["codCBO"] == code]
                    .groupby(group_by)
                    .median(numeric_only=True),
                    2,
                )[return_data]
            )
            data[code] = {
                dataframe.loc[dataframe["codCBO"] == code]["role"].iloc[0]: tmp_
            }

        return data

    @staticmethod
    def create_dataframe_to_dashboard(
        datadict: dict, result_column_name: str
    ) -> pd.DataFrame:
        codes = list()
        roles = list()
        fields = list()
        factors = list()
        for code, first_dict_data in datadict.items():
            for role, second_dict_data in first_dict_data.items():
                for field_knowledge, importance in second_dict_data.items():
                    codes.append(code)
                    roles.append(role)
                    fields.append(field_knowledge.capitalize())
                    factors.append(importance)

        data_ = pd.DataFrame([codes, roles, fields, factors]).T
        data_.columns = ["codCBO", "role", "field_knowledge", result_column_name]

        return data_

    @staticmethod
    def plotting_graph(
        dataframe: pd.DataFrame, column_factor: str, code: int, title_graph: str
    ) -> sns:
        try:
            plt.figure(figsize=(15, 8))
            sns.barplot(
                data=dataframe.loc[dataframe["codCBO"] == code],
                x=column_factor,
                y="field_knowledge",
            )
            plt.title(
                label=dataframe.loc[dataframe["codCBO"] == code]["role"].iloc[0],
                fontdict={"weight": "bold", "fontsize": 15},
            )
            plt.xlabel(
                f"{title_graph} do Campo do Conhecimento",
                fontdict={"weight": "bold", "fontsize": 12},
            )
            plt.ylabel(
                "Campo do Conhecimento", fontdict={"weight": "bold", "fontsize": 12}
            )
            plt.show()
        except:
            print(
                "Esse código não existe na base de dados atual! Por favor tente outro código."
            )
