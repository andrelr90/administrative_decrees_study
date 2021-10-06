import sqlite3
from datetime import datetime

class DBController:
    conn = None

    @staticmethod
    def start_bd():
        DBController.conn = sqlite3.connect('radar_db')

    @staticmethod
    def save_data(texto_valido, links, ementa, situacao, chefe_de_governo, origem, fonte, link_texto_original, referenda, alteracao, alteracao_full, correlacao, interpretacao, veto, assuntos, classificacao_de_direito, observacao, data_assinatura_ato, num_ato, cod_ident_ato):
        already_saved = DBController.get_already_saved()
        
        c = DBController.conn.cursor()
        values = (texto_valido, links, ementa, situacao, chefe_de_governo, origem, fonte, link_texto_original, referenda, alteracao, alteracao_full, correlacao, interpretacao, veto, observacao, data_assinatura_ato, num_ato, cod_ident_ato)
        if link_texto_original is not None and link_texto_original not in already_saved:
            print("Inserting ", cod_ident_ato)
            c.execute("INSERT INTO Decretos VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)", values)
        else:
            print("Updating ", cod_ident_ato)
            c.execute("UPDATE Decretos SET full_text=?, links=?, ementa=?, situacao=?, chefe_de_governo=?, origem=?, fonte=?, link_texto_original=?, referenda=?, alteracao=?, alteracao_full=?, correlacao=?, interpretacao=?, veto=?, observacao=?, data_assinatura_ato=?, num_ato=? WHERE cod_ident_ato = ?", values)
            c.execute("DELETE FROM Decreto_Assunto WHERE Decreto = ?", (cod_ident_ato, ))
            c.execute("DELETE FROM Decreto_Classificacao_de_direito WHERE Decreto = ?", (cod_ident_ato, ))
        DBController.conn.commit()

        #deal with assuntos and classificacao_de_direito
        c.execute("SELECT Assunto FROM Assuntos")
        assuntos_already_in = c.fetchall()
        assuntos_already_in = [item for t in assuntos_already_in for item in t]
        for assunto in assuntos:
            if(assunto not in assuntos_already_in):
                try:
                    c.execute("INSERT INTO Assuntos VALUES (?)", (assunto,))
                except:
                    print("Assunto already exists.")
            try:
                c.execute("INSERT INTO Decreto_Assunto VALUES (?, ?)", (cod_ident_ato, assunto))
            except:
                print("Decreto_Assunto already exists.")
        DBController.conn.commit()

        c.execute("SELECT Classificacao_de_direito FROM Classificacao_de_direito")
        classificacoes_already_in = c.fetchall()
        classificacoes_already_in = [item for t in classificacoes_already_in for item in t]
        for classificacao in classificacao_de_direito:
            if(classificacao not in classificacoes_already_in):
                c.execute("INSERT INTO Classificacao_de_direito VALUES (?)", (classificacao,))
            try:
                c.execute("INSERT INTO Decreto_Classificacao_de_direito VALUES (?, ?)", (cod_ident_ato, classificacao))
            except:
                print("Decreto_Classificacao_de_direito already exists.")
        DBController.conn.commit()

    @staticmethod
    def get_already_saved():
        c = DBController.conn.cursor()
        c.execute("SELECT link_texto_original FROM Decretos")
        result = c.fetchall()
        result = [item for t in result for item in t]   #turn list of tuples into flat list
        return result

    @staticmethod
    def save_error(link):
        c = DBController.conn.cursor()
        c.execute("INSERT INTO Errors VALUES (?, ?)", (link, datetime.now()))
        DBController.conn.commit()
