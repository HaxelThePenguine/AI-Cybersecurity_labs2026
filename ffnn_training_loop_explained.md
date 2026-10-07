# PyTorch FFNN Training Loop: DataLoader, Validation, and Early Stopping

A questo punto hai già i tre pezzi fondamentali:

```python
model = FFNN(input_size=16, hidden_size=64, output_size=4)

criterion = nn.CrossEntropyLoss()

optimizer = torch.optim.AdamW(
    model.parameters(),
    lr=5e-4
)
```

Ora costruiamo il resto nell'ordine naturale: **DataLoader → training loop → validation → early stopping**.

Per prima cosa, visto che hai già i tensori:

```python
X_train_tensor
y_train_tensor

X_val_tensor
y_val_tensor

X_test_tensor
y_test_tensor
```

li raggruppiamo in `TensorDataset`:

```python
from torch.utils.data import TensorDataset, DataLoader

train_dataset = TensorDataset(
    X_train_tensor,
    y_train_tensor
)

val_dataset = TensorDataset(
    X_val_tensor,
    y_val_tensor
)

test_dataset = TensorDataset(
    X_test_tensor,
    y_test_tensor
)
```

`TensorDataset` praticamente dice:

> la riga `i` di `X_train_tensor` appartiene alla label `i` di `y_train_tensor`.

Quindi se:

```python
X_train_tensor[10]
```

è un flow, allora:

```python
y_train_tensor[10]
```

è la sua classe.

Ora creiamo i batch da 64, come richiesto:

```python
batch_size = 64

train_loader = DataLoader(
    train_dataset,
    batch_size=batch_size,
    shuffle=True
)

val_loader = DataLoader(
    val_dataset,
    batch_size=batch_size,
    shuffle=False
)

test_loader = DataLoader(
    test_dataset,
    batch_size=batch_size,
    shuffle=False
)
```

La cosa interessante è `shuffle=True` solo sul training.

Se hai ~20.000 samples, invece di passare:

\[
20\,000
\]

sample tutti insieme, il modello li vede a gruppi di:

\[
64
\]

Quindi ogni batch ha circa:

```python
X_batch.shape
# torch.Size([64, 16])

y_batch.shape
# torch.Size([64])
```

Il primo ha:

\[
64 \text{ flow} \times 16 \text{ feature}
\]

e il secondo contiene le 64 classi corrette.

Ora arriviamo al vero training.

La struttura minima di **un singolo batch** è questa:

```python
optimizer.zero_grad()

outputs = model(X_batch)

loss = criterion(outputs, y_batch)

loss.backward()

optimizer.step()
```

Queste cinque righe sono praticamente il cuore dell'intero training di una neural network.

`optimizer.zero_grad()` cancella i gradienti del batch precedente.

Poi:

```python
outputs = model(X_batch)
```

fa il forward pass:

\[
[64,16]
\rightarrow
[64,64]
\rightarrow
[64,4]
\]

Quindi:

```python
outputs.shape
```

sarà:

```text
[64, 4]
```

Poi:

```python
loss = criterion(outputs, y_batch)
```

confronta i 4 logits prodotti per ogni sample con la classe vera.

Poi:

```python
loss.backward()
```

calcola:

\[
\frac{\partial L}{\partial W_1},
\frac{\partial L}{\partial b_1},
\frac{\partial L}{\partial W_2},
\frac{\partial L}{\partial b_2}
\]

cioè: **in che direzione dovremmo cambiare ogni parametro per diminuire l'errore?**

Infine:

```python
optimizer.step()
```

AdamW usa quei gradienti e modifica effettivamente i pesi.

Ora mettiamo tutto dentro un'epoch:

```python
model.train()

train_loss = 0.0

for X_batch, y_batch in train_loader:

    optimizer.zero_grad()

    outputs = model(X_batch)

    loss = criterion(outputs, y_batch)

    loss.backward()

    optimizer.step()

    train_loss += loss.item() * X_batch.size(0)

train_loss /= len(train_dataset)
```

`model.train()` dice a PyTorch:

> siamo in modalità training.

Nel nostro modello attuale non cambia praticamente nulla, perché non abbiamo `Dropout` o `BatchNorm`, ma è comunque corretto usarlo.

Questa parte:

```python
for X_batch, y_batch in train_loader:
```

fa automaticamente:

```text
batch 1
batch 2
batch 3
...
```

finché ha visto tutto il training set.

Quando ha visto tutto il training set **una volta**, hai completato:

\[
1\text{ epoch}
\]

Poi dobbiamo fare validation.

Qui c'è una differenza fondamentale: **non dobbiamo aggiornare i pesi**.

Quindi:

```python
model.eval()

val_loss = 0.0

with torch.no_grad():

    for X_batch, y_batch in val_loader:

        outputs = model(X_batch)

        loss = criterion(outputs, y_batch)

        val_loss += loss.item() * X_batch.size(0)

val_loss /= len(val_dataset)
```

`model.eval()` mette il modello in modalità evaluation.

E:

```python
with torch.no_grad():
```

dice:

> non calcolare gradienti, perché qui non dobbiamo fare backpropagation.

Infatti nella validation **non compaiono**:

```python
loss.backward()
optimizer.step()
```

Ed è importantissimo.

Il validation set deve semplicemente rispondere alla domanda:

> "Il modello che ho appena addestrato generalizza anche su dati che non ha usato per modificare i pesi?"

Ora possiamo mettere training e validation insieme:

```python
num_epochs = 100

train_losses = []
val_losses = []

for epoch in range(num_epochs):

    # ========================
    # TRAINING
    # ========================

    model.train()

    train_loss = 0.0

    for X_batch, y_batch in train_loader:

        optimizer.zero_grad()

        outputs = model(X_batch)

        loss = criterion(outputs, y_batch)

        loss.backward()

        optimizer.step()

        train_loss += loss.item() * X_batch.size(0)

    train_loss /= len(train_dataset)


    # ========================
    # VALIDATION
    # ========================

    model.eval()

    val_loss = 0.0

    with torch.no_grad():

        for X_batch, y_batch in val_loader:

            outputs = model(X_batch)

            loss = criterion(outputs, y_batch)

            val_loss += loss.item() * X_batch.size(0)

    val_loss /= len(val_dataset)


    train_losses.append(train_loss)
    val_losses.append(val_loss)


    print(
        f"Epoch {epoch+1}/{num_epochs} | "
        f"Train Loss: {train_loss:.4f} | "
        f"Val Loss: {val_loss:.4f}"
    )
```

Questa è già una training loop perfettamente funzionante.

Manca però la parte richiesta esplicitamente dal testo:

> **early stopping on the validation set**

L'idea è questa.

Immagina:

```text
Epoch       Train loss       Val loss

1             1.10            1.14
10            0.45            0.49
20            0.21            0.27
30            0.12            0.23   <- migliore
40            0.07            0.28
50            0.03            0.35
```

Il training continua a migliorare:

\[
L_{\text{train}}\downarrow
\]

ma dopo epoch 30 la validation peggiora:

\[
L_{\text{val}}\uparrow
\]

Questo è un segnale di **overfitting**.

Quindi impostiamo, ad esempio:

```python
patience = 10
min_delta = 1e-4

best_val_loss = float("inf")
epochs_without_improvement = 0
```

`patience = 10` significa:

> se per 10 epoch consecutive la validation loss non migliora, fermati.

`min_delta = 1e-4` significa che consideriamo miglioramento solo una diminuzione di almeno:

\[
0.0001
\]

Quindi aggiungiamo:

```python
if val_loss < best_val_loss - min_delta:

    best_val_loss = val_loss
    epochs_without_improvement = 0

else:

    epochs_without_improvement += 1


if epochs_without_improvement >= patience:

    print("Early stopping")
    break
```

Il training completo diventa quindi:

```python
num_epochs = 100
patience = 10
min_delta = 1e-4

best_val_loss = float("inf")
epochs_without_improvement = 0

train_losses = []
val_losses = []


for epoch in range(num_epochs):

    # ========================
    # TRAINING
    # ========================

    model.train()

    train_loss = 0.0

    for X_batch, y_batch in train_loader:

        optimizer.zero_grad()

        outputs = model(X_batch)

        loss = criterion(outputs, y_batch)

        loss.backward()

        optimizer.step()

        train_loss += loss.item() * X_batch.size(0)

    train_loss /= len(train_dataset)


    # ========================
    # VALIDATION
    # ========================

    model.eval()

    val_loss = 0.0

    with torch.no_grad():

        for X_batch, y_batch in val_loader:

            outputs = model(X_batch)

            loss = criterion(outputs, y_batch)

            val_loss += loss.item() * X_batch.size(0)

    val_loss /= len(val_dataset)


    train_losses.append(train_loss)
    val_losses.append(val_loss)


    print(
        f"Epoch {epoch+1}/{num_epochs} | "
        f"Train Loss: {train_loss:.4f} | "
        f"Val Loss: {val_loss:.4f}"
    )


    # ========================
    # EARLY STOPPING
    # ========================

    if val_loss < best_val_loss - min_delta:

        best_val_loss = val_loss

        epochs_without_improvement = 0

    else:

        epochs_without_improvement += 1


    if epochs_without_improvement >= patience:

        print(
            f"Early stopping at epoch {epoch+1}"
        )

        break
```

Questa è la versione che ti consiglio di **capire prima**.

Poi c'è un piccolo miglioramento importante: quando troviamo il miglior `val_loss`, dovremmo anche **salvare i pesi di quella epoch**, perché l'ultima epoch prima dell'early stopping non è necessariamente la migliore.

Quello lo aggiungerei come prossimo step: sono letteralmente 3-4 righe, ma prima assicurati che ti sia chiara questa struttura:

\[
\boxed{
\text{epoch}
\rightarrow
\text{train}
\rightarrow
\text{validation}
\rightarrow
\text{early stopping check}
}
\]

e soprattutto il cuore:

\[
\boxed{
\text{zero grad}
\rightarrow
\text{forward}
\rightarrow
\text{loss}
\rightarrow
\text{backward}
\rightarrow
\text{optimizer step}
}
\]

Quello è il ciclo fondamentale che vale praticamente per qualunque rete PyTorch.
