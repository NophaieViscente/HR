import pandas as pd
import numpy as np
import math
from typing import List
import matplotlib.pyplot as plt
import scipy

### Graph Libs ###
from neo4j import GraphDatabase
import networkx as nx


class SendDataNeo4j:
    """
    This class is responsible for sending data to a Neo4j database using the neo4j package.

    Methods
    -------
    _run_query(tx, query: str):
        Runs a query on the Neo4j database.

    _verify_nan(self, value):
        Verifies if a given value is NaN, np.NaN, '', pd.NA or math.nan.

    create_nodes(self, dataframe: pd.DataFrame, label: str, all_columns: bool = True, columns_to_add: List[str] = None):
        Inserts nodes into the Neo4j database from a Pandas DataFrame.

    _create_query_new_nodes(self, columns: List[str], row_data: pd.Series, label: str) -> str:
        Generates a Cypher query to create a new node with the received label and properties based on the received data.

    """

    def __init__(self, uri, user, password):
        """
        Initializes the class with the uri, user and password to connect to the Neo4j database.

        Parameters
        ----------
        uri : str
            URI of the Neo4j database.
        user : str
            Username to authenticate in the Neo4j database.
        password : str
            Password to authenticate in the Neo4j database.
        """
        self.driver = GraphDatabase.driver(uri, auth=(user, password))

    def close(self):
        """
        Closes the connection to the Neo4j database.
        """
        self.driver.close()

    @staticmethod
    def _run_query(tx, query: str):
        """
        Runs a query on the Neo4j database.

        Parameters
        ----------
        tx :
            Session object for the Neo4j database.
        query : str
            Cypher query to be executed in the Neo4j database.

        Returns
        -------
        List of records from the executed query.
        """
        result = tx.run(query)
        return [record for record in result]

    def _verify_nan(self, value):
        """
        Verifies if a given value is NaN, np.NaN, '', pd.NA or math.nan.

        Parameters
        ----------
        value : any type
            Value to be verified.

        Returns
        -------
        Boolean indicating if the value is NaN or not.
        """
        return (
            value is np.nan
            or value is np.NaN
            or value == ""
            or value is pd.NA
            or (type(value) is float and math.isnan(value))
        )

    def create_nodes(
        self,
        dataframe: pd.DataFrame,
        label: str,
        all_columns: bool = True,
        columns_to_add: List[str] = None,
    ) -> None:
        """
        This method creates nodes in Neo4j from a pandas DataFrame.

        Parameters:
        -----------
        dataframe : pd.DataFrame
            The DataFrame containing the data to be inserted as nodes in Neo4j.
        label : str
            The label to be used in the Neo4j nodes.
        all_columns : bool, optional
            Flag indicating whether to include all columns from the DataFrame (default is True).
        columns_to_add : List[str], optional
            A list of column names to be included in the nodes (default is None).
        """
        if all_columns:
            for index, row in dataframe.iterrows():
                with self.driver.session() as session:
                    response = session.execute_write(
                        self._run_query,
                        self._create_query_new_nodes(
                            columns=dataframe.columns, row_data=row, label=label
                        ),
                    )
                    print(f">>> Save Line: {index}, Label: {label}")
        else:
            for index, row in dataframe[columns_to_add].iterrows():
                with self.driver.session() as session:
                    response = session.execute_write(
                        self._run_query,
                        self._create_query_new_nodes(
                            columns=dataframe[columns_to_add].columns,
                            row_data=row,
                            label=label,
                        ),
                    )
                    print(f">>> Save Line: {index}, Label: {label}")

    def _create_query_new_nodes(
        self, columns: List[str], row_data: pd.Series, label: str
    ) -> str:
        """
        This method receives a list of columns, a Pandas series containing the data to be inserted in the graph, and a label to
        define the node label. It generates a Cypher query to create a new node with the received label and properties based on
        the received data.

        Parameters:

        columns (List[str]): a list of columns representing the properties of the node.
        row_data (pd.Series): a Pandas series containing the data to be inserted in the graph.
        label (str): a string representing the label of the node.
        Returns:

        query (str): a Cypher query to create a new node with the received label and properties based on the received data.
        """
        query = f"MERGE (n: {label} " + "{"
        for index_columns in range(len(columns)):
            column = columns[index_columns]
            if self._verify_nan(row_data[column]):
                continue
            elif str(row_data[column]).startswith("["):
                query += " SET" + column + " = " + str(row_data[column]) + " ,"
            elif type(row_data[column]) is int:
                query += " " + column + " : toInteger(" + str(row_data[column]) + ") ,"
            elif type(row_data[column]) is float:
                query += " " + column + " : toFloat(" + str(row_data[column]) + ") ,"
            else:
                query += " " + column + " : '" + str(row_data[column]) + "' ,"
        query = query[:-1]
        query += " })"
        return query

    def _format_query_edges(
        self,
        label_node: str,
        label_node2: str,
        search_property_node: str,
        search_property_node2: str,
        property_node: str,
        property_node2: str,
        relationship_name: str,
        property_in_edge: bool = False,
        property_edge: str = None,
        weigth_edge: float = None,
    ):
        """
        Format and return a Cypher query string for creating a relationship between two nodes.

        Parameters:
            label_node (str): The label of the first node.
            label_node2 (str): The label of the second node.
            search_property_node (str): The property used to find the first node.
            search_property_node2 (str): The property used to find the second node.
            property_node (str): The value of the property used to find the first node.
            property_node2 (str): The value of the property used to find the second node.
            relationship_name (str): The name of the relationship between the two nodes.
            property_in_edge (bool): Whether to add a property to the relationship.
            property_edge (str): The name of the property to add to the relationship.
            weight_edge (float): The value of the property to add to the relationship.

        Returns:
            str: The formatted Cypher query string.
        """
        if property_in_edge:
            query = f"""MATCH (a:{label_node}),(b:{label_node2}) 
            WHERE a.{search_property_node} = '{property_node}' AND b.{search_property_node2} = '{property_node2}' 
            MERGE (a)-[r:{relationship_name} {{{property_edge} : {weigth_edge}}}]-(b)"""
            return query
        query = f"""MATCH (a:{label_node}),(b:{label_node2}) 
        WHERE a.{search_property_node} = '{property_node}' AND b.{search_property_node2} = '{property_node2}' 
        MERGE (a)-[r:{relationship_name}]-(b)"""
        return query

    def send_edges_neo4j(
        self,
        dataframe: pd.DataFrame,
        label_node: str,
        label_node2: str,
        search_property_node: str,
        search_property_node2: str,
        property_node: str,
        property_node2: str,
        relationship_name: str,
        property_in_edge: bool = False,
        property_edge: str = None,
        weigth_edge: float = None,
    ):
        """
        Send node edges to a Neo4j database.

        Parameters:
        dataframe (pd.DataFrame): Dataframe with the data to be saved as edges.
        label_node (str): Label of the first node to be connected.
        label_node2 (str): Label of the second node to be connected.
        search_property_node (str): Property name of the first node used in the WHERE clause.
        search_property_node2 (str): Property name of the second node used in the WHERE clause.
        property_node (str): Property value of the first node used in the WHERE clause.
        property_node2 (str): Property value of the second node used in the WHERE clause.
        relationship_name (str): Name of the relationship between the two nodes.
        property_in_edge (bool): Flag indicating if a property should be added to the relationship.
        property_edge (str): Name of the property to be added to the relationship.
        weigth_edge (float): Value of the property to be added to the relationship.

        Returns:
        None
        """
        for index, row_data in dataframe.iterrows():
            with self.driver.session() as session:
                response = session.execute_write(
                    self._run_query,
                    self._format_query_edges(
                        label_node=label_node,
                        label_node2=label_node2,
                        search_property_node=search_property_node,
                        search_property_node2=search_property_node2,
                        property_node=row_data[property_node],
                        property_node2=row_data[property_node2],
                        relationship_name=relationship_name,
                        property_in_edge=property_in_edge,
                        property_edge=property_edge,
                        weigth_edge=row_data[weigth_edge],
                    ),
                )
                print(f">> Save edge {index}")


class GraphBuilder:
    """
    This module provides a GraphBuilder class to interact with a Neo4j graph database and build a NetworkX graph based on the retrieved data.

    Classes:

    GraphBuilder: Provides methods to connect to a Neo4j database, execute Cypher queries and build a NetworkX graph based on the retrieved data.
    Methods:

    init(self, uri, user, password): Initializes the class with the uri, user and password to connect to the Neo4j database.
    close(self): Closes the connection to the Neo4j database.
    _run_query(tx, query: str): Runs a query on the Neo4j database.
    build (self, query:str, limit_entities_return:int=200) -> nx : Builds a NetworkX graph based on the retrieved data from the Neo4j database.
    """

    def __init__(self, uri, user, password):
        """
        Initializes the class with the uri, user and password to connect to the Neo4j database.

        Parameters
        ----------
        uri : str
            URI of the Neo4j database.
        user : str
            Username to authenticate in the Neo4j database.
        password : str
            Password to authenticate in the Neo4j database.
        """
        self.driver = GraphDatabase.driver(uri, auth=(user, password))

    def close(self):
        """
        Closes the connection to the Neo4j database.
        """
        self.driver.close()

    def build(
        self,
        property_node: str,
        query: str,
        limit_return: bool = True,
        limit_entities_return: int = 200,
    ) -> nx:
        """
        Builds a graph using the networkx library.

        Parameters:
            property_node (str): The name of the node property to use as the node label.
            query (str): The Cypher query to be executed in the Neo4j database.
            limit_entities_return (int, optional): Maximum number of nodes to return in the graph (default is 200).

        Returns:
            A graph object.
        """
        if limit_return:
            query += f" LIMIT {limit_entities_return}"

        response = self.driver.session().run(query)

        G = nx.Graph()

        nodes = list(response.graph()._nodes.values())
        for node in nodes:
            G.add_node(
                node._properties[property_node],
                labels=node._labels,
                properties=node._properties,
            )

        rels = list(response.graph()._relationships.values())
        for rel in rels:
            G.add_edge(
                rel.nodes[0]._properties[property_node],
                rel.nodes[1]._properties[property_node],
                key=rel.element_id,
                type=rel.type,
                properties=rel._properties,
            )

        pos = nx.spring_layout(G)
        plt.figure(figsize=(25, 8))
        nx.draw(
            G, pos, with_labels=True, width=0.8, node_color="lightblue", node_size=2500
        )

        self.close()
        plt.show()

        return G
