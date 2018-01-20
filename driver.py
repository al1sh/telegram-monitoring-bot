from keras.layers.core import Dense, Activation, Dropout
from keras.layers.recurrent import LSTM
from keras.models import Sequential
import lstm, time #helper libraries

prediction_interval = 10

# Load Data
X_train, y_train, X_test, y_test = lstm.load_data('prices.csv', prediction_interval, True)

# Build Model
model = Sequential()

model.add(LSTM(
    input_dim=1,
    output_dim=prediction_interval,
    return_sequences=True))
model.add(Dropout(0.2))

model.add(LSTM(
    100,
    return_sequences=False))
model.add(Dropout(0.2))

model.add(Dense(
    output_dim=1))
model.add(Activation('linear'))

start = time.time()
model.compile(loss='mse', optimizer='rmsprop')
print('compilation time : ', time.time() - start)

# Train the model
model.fit(
    X_train,
    y_train,
    batch_size=512,
    nb_epoch=1,
    validation_split=0.05)

# Plot
predictions = lstm.predict_sequences_multiple(model, X_test, prediction_interval, prediction_interval)
lstm.plot_results_multiple(predictions, y_test, prediction_interval)