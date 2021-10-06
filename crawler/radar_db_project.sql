BEGIN TRANSACTION;
CREATE TABLE IF NOT EXISTS `Errors` (
	`link`	TEXT,
	`datetime`	TEXT,
	PRIMARY KEY(`link`,`datetime`)
);
CREATE TABLE IF NOT EXISTS `Decretos` (
	`full_text`	TEXT,
	`links`	TEXT DEFAULT NULL,
	`ementa`	TEXT DEFAULT NULL,
	`situacao`	TEXT DEFAULT NULL,
	`chefe_de_governo`	TEXT DEFAULT NULL,
	`origem`	TEXT DEFAULT NULL,
	`fonte`	TEXT DEFAULT NULL,
	`link_texto_original`	TEXT,
	`referenda`	TEXT DEFAULT NULL,
	`alteracao`	TEXT DEFAULT NULL,
	`alteracao_full`	TEXT,
	`correlacao`	TEXT DEFAULT NULL,
	`interpretacao`	TEXT DEFAULT NULL,
	`veto`	TEXT DEFAULT NULL,
	`observacao`	TEXT DEFAULT NULL,
	`data_assinatura_ato`	TEXT DEFAULT NULL,
	`num_ato`	TEXT DEFAULT NULL,
	`cod_ident_ato`	TEXT,
	PRIMARY KEY(`cod_ident_ato`)
);
CREATE TABLE IF NOT EXISTS `Decreto_Classificacao_de_direito` (
	`Decreto`	TEXT,
	`Classificacao_de_direito`	TEXT,
	PRIMARY KEY(`Decreto`,`Classificacao_de_direito`),
	FOREIGN KEY(`Decreto`) REFERENCES `Decretos`(`cod_ident_ato`),
	FOREIGN KEY(`Classificacao_de_direito`) REFERENCES `Classificacao_de_direito`(`Classificacao_de_direito`)
);
CREATE TABLE IF NOT EXISTS `Decreto_Assunto` (
	`Decreto`	TEXT,
	`Assunto`	TEXT,
	FOREIGN KEY(`Decreto`) REFERENCES `Decretos`(`cod_ident_ato`),
	PRIMARY KEY(`Decreto`,`Assunto`)
);
CREATE TABLE IF NOT EXISTS `Classificacao_de_direito` (
	`Classificacao_de_direito`	TEXT,
	PRIMARY KEY(`Classificacao_de_direito`)
);
CREATE TABLE IF NOT EXISTS `Assuntos` (
	`Assunto`	TEXT,
	PRIMARY KEY(`Assunto`)
);
COMMIT;
