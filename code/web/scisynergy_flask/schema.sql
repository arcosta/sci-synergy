CREATE TABLE IF NOT EXISTS resposta (
	id	SERIAL,
	idusuario	INTEGER NOT NULL,
	idquestao	TEXT NOT NULL,
	conteudo	TEXT
)
