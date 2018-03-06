package edu.hpi.minorthird.wrapper;

import edu.cmu.minorthird.classify.*;
import edu.cmu.minorthird.classify.experiments.Evaluation;
import edu.cmu.minorthird.classify.sequential.*;
import edu.cmu.minorthird.util.IOUtil;

import java.io.File;
import java.io.FileWriter;
import java.io.IOException;

public class Main {

    private CollinsPerceptronLearner cp;
    private String modelFileName;
    private String dataFileName;
    private SequenceDataset ds;
    private SequenceClassifier sc;
    private int historyLength;


    private Main() {
        this.cp = null;
    }

    private void usage() {
        System.out.println("Usage:");
        System.out.println("  train <int:historylen> <str:data-file> <str:model-file> <int:epochs>  ");
        System.out.println("  test  <int:historylen> <str:data-file> <str:model-file> <str:out-file>");
    }

    private void loadDataSet() throws IOException {
        this.ds = DatasetLoader.loadSequence(new File(this.dataFileName));
        this.ds.setHistorySize(this.historyLength);
    }

    private void loadClassifier() throws IOException {
        this.sc = (SequenceClassifier) IOUtil.loadSerialized(new File(this.modelFileName));
    }

    private void saveClassifier() throws IOException {
        IOUtil.saveSomehow(this.sc, new File(this.modelFileName));
    }

    public static void main(String[] args) throws IOException {
        Main m = new Main();

        if (args.length == 5) {
            m.historyLength = Integer.parseInt(args[1]);
            m.dataFileName = args[2];
            m.modelFileName = args[3];

            m.loadDataSet();

            if(args[0].matches("train")) {
                int epochs = Integer.parseInt(args[4]);
                m.train(epochs);
            } else if (args[0].matches("test")) {
                String outputFileName = args[4];
                m.predict(outputFileName);
            } else {
                m.usage();
            }
        } else {
            m.usage();
        }

    }

    private void train(int numEpochs) throws IOException {
        //System.out.println("train");
        this.cp = new CollinsPerceptronLearner(this.historyLength, numEpochs);

        this.sc = this.cp.batchTrain(this.ds);
        //System.out.println(((CMM) this.sc).getClassifier());
        this.saveClassifier();
    }

    private void predict(String outputFileName) throws IOException {
        this.loadClassifier();

        Evaluation eval = new Evaluation(this.ds.getSchema());
        eval.extend(this.sc, this.ds);
        File f = new File(outputFileName);
        FileWriter fw = new FileWriter(f);
        fw.write(eval.toString());
        fw.close();

    }
}
