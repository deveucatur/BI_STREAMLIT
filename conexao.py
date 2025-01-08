import mysql.connector


def conexaoBD():

    conexao = mysql.connector.connect(
        passwd='6Kp62muMRD@!1',
        port=3306,
        user='root',
        host='192.168.0.7',
        database='projeu'
    )
    
    return conexao