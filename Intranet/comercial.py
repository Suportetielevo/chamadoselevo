import streamlit as st
import mysql.connector
import pandas as pd

# Conexão com o banco de dados
meubd = mysql.connector.connect(
    host='monolito-elevo-prod20200927172408180600000028.cv0onkc8ijpz.us-east-2.rds.amazonaws.com',
    user='monolito',
    password='1642gEkdWYtQ',
    database='monolito'
)

cursor = meubd.cursor()

# Executa a consulta SQL
cursor.execute("""
select p.id            as ID_PROJETO,
       c.name          as CLIENTE,
       c2.name         as CIDADE_CLIENTE,
       p2.name         as ESTADO_CLIENTE,
       u.name          as CONSULTOR,
       u2.name         as CONSULTOR_EXTERNO,
       ppt.description as FORMA_DE_PAGAMENTO,
       fr.VALOR_SOMADO as VALOR_RECEBIMENTO,
       r.created_at as DATA_FATURAMENTO,
       pi.created_at   as DATA_PGMTO_CONFIRMADO
from projects p
         join clients c on p.client_id = c.id
         join franchises f on p.franchise_id = f.id
         join users u on f.user_id = u.id
         left join outsider_franchises o on p.outsider_franchise_id = o.id
         left join users u2 on o.user_id = u2.id
         join cities c2 on c.city_id = c2.id
         join provinces p2 on c2.province_id = p2.id
         join financings f2 on p.id = f2.project_id and f2.status_id not in (123)
         left join (select sum(fr.value) as VALOR_SOMADO, fr.id, fr.financing_id
                    from financing_recipes fr
                    where fr.active = 1
                    group by fr.financing_id) fr on fr.financing_id = f2.id
         join module_contracts mc on p.id = mc.project_id
         join revenues r on p.id = r.project_id
         join project_interactions pi
              on p.id = pi.project_id and pi.type = 'status_change' and pi.comment = 'PAGAMENTO CONFIRMADO'
         join project_payment_types ppt on p.payment_type_id = ppt.id
group by p.id
order by pi.created_at

""")

# Obter os dados
dados = cursor.fetchall()

# Criar um DataFrame do Pandas
df = pd.DataFrame(dados, columns=[desc[0] for desc in cursor.description])

# Fechar a conexão com o banco de dados
cursor.close()
meubd.close()

# Título do Dashboard
st.title('Projetos por Consultor ')

# Exibir a tabela com os dados
st.dataframe(df)
