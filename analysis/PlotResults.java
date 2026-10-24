import org.jfree.chart.*;
import org.jfree.chart.axis.*;
import org.jfree.chart.plot.*;
import org.jfree.chart.renderer.xy.*;
import org.jfree.data.xy.*;
import java.awt.*;
import java.awt.geom.*;
import java.awt.image.BufferedImage;
import javax.imageio.ImageIO;
import java.io.*;
import java.nio.file.*;
import java.util.*;
import java.util.List;

/** Publication chart from recorded runs.csv. JFreeChart 1.5.5; no synthetic samples. */
public class PlotResults {
  static Color green = new Color(12, 115, 89), navy = new Color(30, 56, 80);
  static List<Map<String,Double>> rows = new ArrayList<>();
  static int[] threads = {1,8,32,64};
  static double median(List<Double> data) { Collections.sort(data); return data.get(data.size()/2); }
  static JFreeChart chart(String title, String unit, String[] columns, String[] labels) {
    XYSeriesCollection dataset = new XYSeriesCollection();
    for(int c=0;c<columns.length;c++) {
      XYSeries medians = new XYSeries(labels[c]+" median");
      XYSeries samples = new XYSeries(labels[c]+" repeats");
      for(int n=0;n<threads.length;n++) {
        List<Double> values = new ArrayList<>();
        for(Map<String,Double> row:rows) if(row.get("threads").intValue()==threads[n]) values.add(row.get(columns[c]));
        medians.add(n,median(new ArrayList<>(values)));
        for(int r=0;r<values.size();r++) samples.add(n+(r-1)*0.045, values.get(r));
      }
      dataset.addSeries(medians); dataset.addSeries(samples);
    }
    SymbolAxis x = new SymbolAxis("Client threads", new String[]{"1","8","32","64"});
    x.setGridBandsVisible(false); x.setRange(-0.25,3.25);
    NumberAxis y = new NumberAxis(unit); y.setAutoRangeIncludesZero(true);
    for(ValueAxis axis:new ValueAxis[]{x,y}) {
      axis.setLabelFont(new Font("SansSerif",Font.PLAIN,24));
      axis.setTickLabelFont(new Font("SansSerif",Font.PLAIN,22));
      axis.setAxisLinePaint(new Color(210,215,215));
    }
    XYLineAndShapeRenderer renderer = new XYLineAndShapeRenderer();
    for(int c=0;c<columns.length;c++) {
      Color col = c==0?green:navy;
      renderer.setSeriesPaint(c*2,col);
      renderer.setSeriesStroke(c*2,new BasicStroke(3.5f));
      renderer.setSeriesShape(c*2,new Ellipse2D.Double(-5,-5,10,10));
      renderer.setSeriesLinesVisible(c*2,true);
      renderer.setSeriesPaint(c*2+1,new Color(col.getRed(),col.getGreen(),col.getBlue(),125));
      renderer.setSeriesShape(c*2+1,new Ellipse2D.Double(-6,-6,12,12));
      renderer.setSeriesLinesVisible(c*2+1,false);
      renderer.setSeriesVisibleInLegend(c*2+1,false);
    }
    XYPlot plot = new XYPlot(dataset,x,y,renderer);
    plot.setBackgroundPaint(Color.WHITE); plot.setOutlineVisible(false);
    plot.setDomainGridlinesVisible(false); plot.setRangeGridlinePaint(new Color(226,232,230));
    JFreeChart result = new JFreeChart(title,new Font("SansSerif",Font.BOLD,29),plot,true);
    result.setBackgroundPaint(Color.WHITE); result.getLegend().setItemFont(new Font("SansSerif",Font.PLAIN,22));
    result.setPadding(new org.jfree.chart.ui.RectangleInsets(20,20,20,20));
    return result;
  }
  public static void main(String[] args) throws Exception {
    List<String> lines=Files.readAllLines(Path.of(args[0])); String[] headers=lines.get(0).split(",");
    for(String line:lines.subList(1,lines.size())) {
      String[] cells=line.split(","); Map<String,Double> row=new HashMap<>();
      for(int i=0;i<headers.length;i++) try {row.put(headers[i],Double.parseDouble(cells[i]));}catch(NumberFormatException ignored){}
      rows.add(row);
    }
    if(rows.size()!=12) throw new IllegalArgumentException("Expected all 12 recorded runs");
    BufferedImage image=new BufferedImage(2200,1100,BufferedImage.TYPE_INT_RGB);
    Graphics2D g=image.createGraphics();g.setColor(Color.WHITE);g.fillRect(0,0,2200,1100);
    g.setRenderingHint(RenderingHints.KEY_ANTIALIASING,RenderingHints.VALUE_ANTIALIAS_ON);
    g.setColor(navy);g.setFont(new Font("SansSerif",Font.BOLD,42));
    g.drawString("MongoDB under load: throughput and tail latency",60,72);
    g.setFont(new Font("SansSerif",Font.PLAIN,25));g.setColor(new Color(90,105,110));
    g.drawString("100,000 records  ·  95% reads / 5% updates  ·  2-CPU server quota  ·  3 × 30-second runs",60,119);
    chart("Completed operations", "Operations / second",new String[]{"throughput_ops_s"},new String[]{"Throughput"})
      .draw(g,new Rectangle2D.Double(35,170,1045,755));
    chart("Successful-operation p99", "Milliseconds",new String[]{"read_p99_ms","update_p99_ms"},new String[]{"Read","Update"})
      .draw(g,new Rectangle2D.Double(1120,170,1045,755));
    g.setFont(new Font("SansSerif",Font.PLAIN,24));g.setColor(new Color(80,95,100));
    g.drawString("Lines connect medians; translucent dots show every repeat. No failed read/update operations in these runs.",60,993);
    g.drawString("Source: recorded YCSB 0.17.0 results, MongoDB 8.0.34, Docker Desktop / WSL2. Local experiment by Amit Wani.",60,1036);
    g.dispose();ImageIO.write(image,"png",new File(args[1]));
    File outputDir=new File(args[1]).getAbsoluteFile().getParentFile();
    ChartUtils.saveChartAsPNG(new File(outputDir,"throughput-by-threads.png"),
      chart("More threads complete more operations", "Operations / second",new String[]{"throughput_ops_s"},new String[]{"Throughput"}),1200,800);
    ChartUtils.saveChartAsPNG(new File(outputDir,"latency-by-threads.png"),
      chart("The tail-latency cost of concurrency", "p99 latency (milliseconds)",new String[]{"read_p99_ms","update_p99_ms"},new String[]{"Read","Update"}),1200,800);
  }
}
