import edu.illinois.cs.cogcomp.lbj.chunk.Chunker;

import LBJ2.nlp.seg.PlainToTokenParser;
import LBJ2.nlp.Sentence;
import LBJ2.nlp.SentenceSplitter;
import LBJ2.nlp.Word;
import LBJ2.nlp.WordSplitter;
import LBJ2.parse.Parser;

import java.io.InputStreamReader;
import java.io.BufferedReader;


public class FixedLBJChunker 
{
  public static class StdInParser implements Parser 
  {
    private BufferedReader reader;

    public StdInParser() { 
      reader = new BufferedReader(new InputStreamReader(System.in));
    }

    public Object next() {
      try {
        String str = reader.readLine();
        if (str != null) {
          return new Sentence(str.trim());
        }
      } catch (Exception e) {
        return null;
      }
      return null;
    }
    
    public void reset() { }
                                  
    public void close() { }
  }

  public static void main(String[] args) {
    String filename = null;

    try {
      if (args.length > 1) throw new Exception();
    }
    catch (Exception e) {
      System.err.println("usage: java FixedLBJChunker < input_file.txt");
      System.exit(1);
    }

    Chunker chunker = new Chunker();
    Parser parser =
      new PlainToTokenParser(
          new WordSplitter(new StdInParser()));
    String previous = "";

    for (Word w = (Word) parser.next(); w != null; w = (Word) parser.next()) {
      String prediction = chunker.discreteValue(w);
      if (prediction.startsWith("B-")
          || prediction.startsWith("I-")
             && !previous.endsWith(prediction.substring(2))) {
        System.out.print("[" + prediction.substring(2) + " ");
      }
      System.out.print("(" + w.partOfSpeech + " " + w.form + ") ");
      if (!prediction.equals("O")
          && (w.next == null
              || chunker.discreteValue(w.next).equals("O")
              || chunker.discreteValue(w.next).startsWith("B-")
              || !chunker.discreteValue(w.next)
                  .endsWith(prediction.substring(2)))) {
        System.out.print("] ");
      }
      if (w.next == null) {
        System.out.println();
      }
      previous = prediction;
    }
  }
}
