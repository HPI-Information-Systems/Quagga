import java.io.File;
import java.io.IOException;
import java.text.ParseException;

import jangada.*;

import edu.cmu.minorthird.text.MutableTextLabels;
import edu.cmu.minorthird.text.TextBaseLoader;
import edu.cmu.minorthird.text.gui.TextBaseEditor;
import edu.cmu.minorthird.util.LineProcessingUtil;

/**
 * Example of the usage of ReplyTo annotator and SigFileAnnotator.
 * @author  Vitor R. Carvalho
 * June 2005
 * 
 * Useful when performing tasks using minorthird's world. Displays 
 * a GUI with the messages and associated Signature and Reply annotations 
 * 
 * Usage: Demo directoryName
 * 
 * Please use 1 email message per file. Please use .eml format.
 * 
 * @param directory where your email files are.
 */
public class Demo6 {

	public static void main(String[] args) {

		if (args.length != 1) {
			System.out.println("Usage: \n");
			System.out.println("Demo directoryWithFiles\n");
			return;
		}
		String dirname = args[0];//test directory
		//load directory with files with annotations
		//and create TextLabels.
		TextBaseLoader tbl = new TextBaseLoader(TextBaseLoader.DOC_PER_FILE,
				true);
		try {
			tbl.load(new File(dirname));
		} catch (IOException e) {
			e.printStackTrace();
		} catch (ParseException e) {
			e.printStackTrace();
		}
		MutableTextLabels labels = tbl.getLabels();

		//create a SignatureFile annotator and - annotate the lines
		//containing a signature with the "sig" lable
		SigFileAnnotator sigAnnot = new SigFileAnnotator();
		sigAnnot.doAnnotate(labels);

		//create a ReplyTo annotator and annotate with the "reply" label
		ReplyToAnnotator repAnnot = new ReplyToAnnotator();
		repAnnot.doAnnotate(labels);

		//visualize the annotations
		TextBaseEditor.edit(labels, new File("foo"));
	}
}
