import edu.cmu.minorthird.text.CharAnnotation;
import edu.cmu.minorthird.util.LineProcessingUtil;
import jangada.*;

/**
 * An example of how to extract the reply-lines(quotes) of a message 
 * or, a message with the reply-lines removed.
 * 
 * Created on Jun 12, 2005
 * @author Vitor R. Carvalho
 * 
 * Please use 1 email message per file. Please use .eml format.
 * 
 * Usage: Demo3 filename1 filename2 filename3
 * Usage: Demo3 directoryname\*
 * 
 */
public class Demo3 {
	
	public static void main(String[] args) {
		
		if (args.length < 1) {
			System.out.println("Usage: \n");
			System.out.println("Demo3 filename1 filename2 filename3 \n");
			System.out.println("Demo3 directoryWithFiles\\*\n");
			return;
		}
		
		ReplyToAnnotator repto = new ReplyToAnnotator();
		try {
			for (int i = 0; i < args.length; i++) {
				String message = LineProcessingUtil.readFile(args[i]);
				CharAnnotation[] onelist = repto.annotateString(message);
				
				//to print the reply-to lines
				String onelist3 = repto.getMsgReplyLines(message);
				System.out.println("\n######### Reply Lines of " + args[i]
																		+ " #######");
				System.out.print(onelist3.toString());
				
				//in case you want to print the message with the 
				//reply-lines removed, just uncommend the code below
				
				//	      	 	 System.out.println("\n######### Msg After Removing the Reply Lines  #######");
				//	      	 	 String onelist2 = repto.deleteReplyLinesFromMsg(message);
				//	  		     System.out.print(onelist2.toString()+"\n\n"); 
			}
		} catch (Exception e) {
			e.printStackTrace();
		}
	}
	
}
