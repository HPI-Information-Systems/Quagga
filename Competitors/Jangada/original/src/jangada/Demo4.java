package jangada;

import edu.cmu.minorthird.text.CharAnnotation;
import edu.cmu.minorthird.util.LineProcessingUtil;

/**
 * This class is another example of how to extract the reply-lines(quotes) of a message 
 * ; Or a message with the reply-lines removed.
 * 
 * Created on Jun 12, 2005
 * @author Vitor R. Carvalho
 *  
 * The simplest way, pass an email msg as a String, and have returned a String
 * with the reply-to lines only (or a String with the original msg without the
 * reply-to lines)
 * 
 * Please use 1 email message per file. Please use .eml format.
 *  
 */
public class Demo4 {
	
	public static void main(String[] args) {
		
		if (args.length < 1) {
			System.out.println("Usage: \n");
			System.out.println("Demo4 filename1 filename2 filename3 \n");
			System.out.println("Demo4 directoryWithFiles\\*\n");
			return;
		}
		
		ReplyToAnnotator repto = new ReplyToAnnotator();				
		try {
			for (int i = 0; i < args.length; i++) {
				//read the msg file
				String message = LineProcessingUtil.readFile(args[i]);
								
				//extract, and print the reply-to lines
				String msg = repto.getMsgReplyLines(message);
				System.out.println("\n######### Reply Lines of " + args[i]+ " #######");
				System.out.print(msg);
				
				
				
				
				//in case you want to print the message with the 
				//reply-lines removed, just uncommend the code below
				
//				String msg = repto.deleteReplyLinesFromMsg(message);
//				System.out.println("\n######### Msg After Removing the Reply Lines  #######");
//				System.out.print(msg);
				 
			}
		} catch (Exception e) {
			e.printStackTrace();
		}
	}
	
}