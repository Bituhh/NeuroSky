# NeuroSky

This project is part of my Final 3rd Year Project. I am attempting to train a Machine Learning Algorithm to classify
action from a EEG live recording incrementally, I am attempting utilise the following ML algorithms to do this:

 - Random Forrest
 - Multi Layer Perceptron - MLP

## Instructions:

The library is split into 3 sections:
- Connector
    - The connector reaches to the ThinkGear Connector (NeuroSky Device) utilising the socket library, and returns the raw output from the 'data' Observable.
    `connector = Connector(debug=False, verbose=False)`
- Processor
    - The processor transforms the raw_data into fft_data. `processor = Processor()`
- Trainer
    - It trains the device utilising Random Forrest. `trainer = Trainer()`

The whole project is designed in a reactive programming style by utilising the RxPy library to 
create Observables and Subjects. Both the Connector and Processor contains a Subject labeled data in which
you are able to subscribe to any changes.

```
connector = Connector() # Connector assumes debug and verbose to be False.
processor = Proccessor()
trainer = Trainer()

# Calling async subscribers.
connector.data.subscribe(processor.add_data) # using named method.
processor.data.subscribe(lambda data: trainer.add_data(data)) # using anonymous lambda method. 

trainer.train() # Implement training trigger -> use with key press or button clicked.
trainer.predict() # Predict data

# Always close at end of application.
# It releases resource from the RxPy subscriptions.
connector.close()
processor.close()
trainer.close()
# Class will have to be reassigned if you wish to subscribe after calling close.
```
 
## Contact Info:
For any further details on this project feel free to contact me at:

Email: Victor@Oliveira.org.uk

LinkedIn: [Victor Oliveira](https://www.linkedin.com/in/vcoliveira)

Thank you.
