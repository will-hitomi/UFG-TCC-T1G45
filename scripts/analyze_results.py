import pandas as pd
import matplotlib.pyplot as plt

# carregar resultados
df = pd.read_csv("data/evaluation_results.csv")

# calcular média por item
df["media"] = df[["clareza","completude","aderencia","padronizacao"]].mean(axis=1)

print("\nTabela de resultados:")
print(df)

# média geral
media_geral = df["media"].mean()

print("\nMédia geral do sistema:", round(media_geral,2))

# gráfico
df.plot(
    x="item",
    y="media",
    kind="bar",
    legend=False,
    title="Avaliação média por item"
)

plt.ylabel("Nota média")
plt.tight_layout()
plt.show()
