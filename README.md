This repository has the code used to run the experiments in the paper titled "A Framework for Balancing Power Grid Efficiency and Risk with Bi-objective Stochastic Integer Optimization." Please contact Ramsey Rossmann (rossmann2@wisc.edu) for questions regarding the included code.

After cloning, do the following to begin running the basic experiments.

Data:
Toy examples (train size "tiny" and test size "small") are included. Larger instances are not due to file size but can be created by doing the follow:
1. bash bigfilesetup.sh: this will un-tar a file and combine a few .npy arrays that have been split to be less than 100 MB
2. bash make_train-scenarios.sh: makes S.pkl for training size and model defined in file
3. bash make_test_data.sh: makes S.pkl for test size defined in file
4. makeOff.py: makes off.pkl for existing training and test S.pkl

To solve model: run-here.py, which will
1. Copy relevant files to new directory named something like "proposal_constraint"
2. Solve each instance (n_trains of them)
3. (If solving a bi-objetive model with the constraint formulation:) evaluate the extreme objective on the training data (since this is not necessarily tight at the end of step 1)
4. Move solution files (data.pkl and solutions.pkl) to correct directories
5. Evaluate each solution
6. Move these results to correct directories
7. Summarize results of steps 1 and 4 into results_table.csv and make some summary plots

Information:
- S.pkl = one training sample with data for the instance
- Sn.pkl = one test sample used for evaluating the normal objective
- Se.pkl = one test sample used for evaluating the extreme objective
- off.pkl = binary on/off simulated data for generators
- "unconditional" in the code refers the bi-objective unconditional model discussed in the paper
- "proposal" in the code refers the bi-objective conditional model
- "base" and "independent" match their names in the paper


The code was written to be run on both a single device (the author's Mac) and on a server (the Center for High Throughput Computing—CHTC—at the University of Wisconsin-Madison). This explains some file and parameter names as well as some file/directory management.
