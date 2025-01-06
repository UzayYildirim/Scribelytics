# Dataset path configuration
datasetUrl = ''

# Import required libraries
import pandas as pd, numpy as np, plotly.express as px, plotly.graph_objects as go, time, os
from IPython.display import display, HTML
import matplotlib.pyplot as plt, seaborn as sns

def print_scribelytics_art():
    art = r"""
  ____            _ _          _       _   _          
 / ___|  ___ _ __(_) |__   ___| |_   _| |_(_) ___ ___ 
 \___ \ / __| '__| | '_ \ / _ \ | | | | __| |/ __/ __|
  ___) | (__| |  | | |_) |  __/ | |_| | |_| | (__\__ \
 |____/ \___|_|  |_|_.__/ \___|_|\__, |\__|_|\___|___/
                                 |___/                
    """
    print(art)


# Main DataAnalyzer class for performing data analysis and visualization
class DataAnalyzer:
    def __init__(self, df, datasetName):
        self.df = df.copy()
        self.figures = []
        self.numericColumns = df.select_dtypes(include=[np.number]).columns
        self.categoricalColumns = df.select_dtypes(exclude=[np.number]).columns
        self.cleaningLog = []
        self.datasetName = datasetName
        self.cleanData()
        self.stats = self._calculateStats()

    # Data cleaning and preprocessing methods
    def cleanData(self):
        initialRows, initialNulls = len(self.df), self.df.isnull().sum().sum()
        self.df.drop_duplicates(inplace=True)
        droppedDuplicates = initialRows - len(self.df)
        if droppedDuplicates > 0:
            self.cleaningLog.append(f"Removed {droppedDuplicates} duplicate rows")
        
        for column in self.df.columns:
            nullCount = self.df[column].isnull().sum()
            if nullCount > 0:
                fillValue = self.df[column].mean() if self.df[column].dtype in ['int64', 'float64'] else self.df[column].mode()[0]
                self.df[column].fillna(fillValue, inplace=True)
                self.cleaningLog.append(f"Filled {nullCount} missing values in '{column}' with {fillValue:.2f if isinstance(fillValue, float) else fillValue}")
        
        self.cleaningLog.extend([f"Total rows: {initialRows} → {len(self.df)}", 
                               f"Total missing values: {initialNulls} → {self.df.isnull().sum().sum()}"])

    def _calculateStats(self):
        stats = {}
        for col in self.numericColumns:
            stats.update({
                f'mean_{col}': float(self.df[col].mean()),
                f'median_{col}': float(self.df[col].median()),
                f'min_{col}': float(self.df[col].min()),
                f'max_{col}': float(self.df[col].max())
            })
        for col in self.categoricalColumns:
            valueCounts = self.df[col].value_counts()
            total = len(self.df)
            stats.update({
                f'percentage_{col}_{value}': float((count/total) * 100)
                for value, count in valueCounts.items()
            })
            stats.update({
                f'total_{col}_{value}': int(count)
                for value, count in valueCounts.items()
            })
        return stats

    # Visualization creation methods
    def _createPlotlyFigure(self, plotType, **kwargs):
        layoutKwargs = {'height': kwargs.pop('height', 400), 'showlegend': kwargs.pop('showlegend', False),
                       'title_x': 0.5, 'title': kwargs.get('title')}
        
        if plotType == 'histogram':
            fig = px.histogram(self.df, marginal='box', opacity=0.7, nbins=30, 
                             color_discrete_sequence=['skyblue'], **kwargs)
        elif plotType == 'box':
            fig = px.box(self.df, color_discrete_sequence=['skyblue'], **kwargs)
        elif plotType == 'bar':
            valueCounts = kwargs.pop('valueCounts')
            fig = go.Figure(data=[go.Bar(x=valueCounts.index, y=valueCounts.values, 
                                       text=valueCounts.values, textposition='auto')])
            layoutKwargs.update({'xaxis_title': kwargs.get('xaxisTitle'), 
                               'yaxis_title': kwargs.get('yaxisTitle')})
        elif plotType == 'pie':
            valueCounts = kwargs.pop('valueCounts')
            fig = px.pie(values=valueCounts.values, names=valueCounts.index, **kwargs)
        elif plotType == 'scatter':
            fig = px.scatter(self.df, trendline="ols", **kwargs)
        elif plotType == 'heatmap':
            corrMatrix = kwargs.pop('corrMatrix')
            fig = go.Figure(data=[go.Heatmap(z=corrMatrix, x=corrMatrix.columns, y=corrMatrix.columns,
                                           text=np.round(corrMatrix, 2), texttemplate='%{text}',
                                           colorscale='RdBu', zmin=-1, zmax=1)])
            layoutKwargs.update({'width': 800, 'height': 800})
        
        fig.update_layout(**layoutKwargs)
        return fig

    def createVisualizations(self):
        print("\nCreating visualizations...")
        try:
            display(HTML("<h3>Creating Distribution Plots...</h3>"))
            for column in self.numericColumns:
                for plotType in ['histogram', 'box']:
                    fig = self._createPlotlyFigure(plotType, x=column if plotType == 'histogram' else None,
                                                 y=column if plotType == 'box' else None,
                                                 title=f'{"Distribution" if plotType == "histogram" else "Box Plot"} of {column}')
                    self.figures.append((f'{plotType}_{column}', fig))
                    plt.figure(figsize=(10 if plotType == 'histogram' else 8, 6))
                    if plotType == 'histogram':
                        sns.histplot(data=self.df, x=column, kde=True)
                    else:
                        sns.boxplot(data=self.df, y=column)
                    plt.title(f'{"Distribution" if plotType == "histogram" else "Box Plot"} of {column}')
                    plt.show()
                    time.sleep(0.5)

            display(HTML("<h3>Creating Categorical Plots...</h3>"))
            for catCol in self.categoricalColumns:
                valueCounts = self.df[catCol].value_counts()
                for plotType in ['bar', 'pie']:
                    plot_kwargs = {
                        'valueCounts': valueCounts,
                        'title': f'{"Count Plot" if plotType == "bar" else "Distribution"} of {catCol}'
                    }
                    if plotType == 'bar':
                        plot_kwargs.update({
                            'xaxisTitle': catCol,
                            'yaxisTitle': 'Count'
                        })
                    
                    fig = self._createPlotlyFigure(plotType, **plot_kwargs)
                    self.figures.append((f'{"count" if plotType == "bar" else "pie"}_{catCol}', fig))
                    plt.figure(figsize=(10 if plotType == 'bar' else 8, 8 if plotType == 'pie' else 6))
                    if plotType == 'bar':
                        sns.countplot(data=self.df, x=catCol)
                        plt.xticks(rotation=45)
                    else:
                        plt.pie(valueCounts.values, labels=valueCounts.index, autopct='%1.1f%%')
                    plt.title(f'{"Count Plot" if plotType == "bar" else "Distribution"} of {catCol}')
                    plt.show()
                    time.sleep(0.5)

            display(HTML("<h3>Creating Relationship Plots...</h3>"))
            for numCol in self.numericColumns:
                for catCol in self.categoricalColumns:
                    fig = self._createPlotlyFigure('box', x=catCol, y=numCol, title=f'{numCol} by {catCol}', color=catCol)
                    self.figures.append((f'relationship_{numCol}_{catCol}', fig))
                    plt.figure(figsize=(12, 6))
                    sns.boxplot(data=self.df, x=catCol, y=numCol)
                    plt.title(f'{numCol} by {catCol}')
                    plt.xticks(rotation=45)
                    plt.show()
                    time.sleep(0.5)

            if len(self.numericColumns) > 1:
                display(HTML("<h3>Creating Correlation Plots...</h3>"))
                corrMatrix = self.df[self.numericColumns].corr()
                for i, col1 in enumerate(self.numericColumns):
                    for col2 in self.numericColumns[i+1:]:
                        fig = self._createPlotlyFigure('scatter', x=col1, y=col2, title=f'{col1} vs {col2}')
                        self.figures.append((f'scatter_{col1}_{col2}', fig))
                        plt.figure(figsize=(10, 6))
                        sns.regplot(data=self.df, x=col1, y=col2)
                        plt.title(f'{col1} vs {col2}')
                        plt.show()
                        time.sleep(0.5)

                fig = self._createPlotlyFigure('heatmap', corrMatrix=corrMatrix, title='Correlation Heatmap')
                self.figures.append(('correlation_heatmap', fig))
                plt.figure(figsize=(10, 8))
                sns.heatmap(corrMatrix, annot=True, cmap='RdBu', center=0)
                plt.title('Correlation Heatmap')
                plt.show()
                time.sleep(0.5)

        except Exception as e:
            print(f"Error creating visualizations: {str(e)}")
            raise

    # HTML report generation methods
    def generateReport(self):
        try:
            self.createVisualizations()
            timestamp = f"{time.strftime('%Y-%m-%d %H:%M:%S %Z')} | Uzay Yildirim"
            
            summaryStats = {
                'Total Records': len(self.df),
                'Total Variables': len(self.df.columns),
                'Numeric Variables': len(self.numericColumns),
                'Categorical Variables': len(self.categoricalColumns)
            }
            
            summaryHtml = ''.join([f'''
                <div class="col-md-3">
                    <div class="alert alert-{['info', 'success', 'warning', 'primary'][i]}">
                        <h4 class="alert-heading">{k}</h4>
                        <h2 class="mb-0">{v:,}</h2>
                    </div>
                </div>''' for i, (k, v) in enumerate(summaryStats.items())])

            findingsHtml = ''.join([f'''
                <li class="list-group-item">
                    <strong>{col}</strong><br>
                    Mean: {self.stats[f'mean_{col}']:,.2f}<br>
                    Median: {self.stats[f'median_{col}']:,.2f}<br>
                    Range: {self.stats[f'min_{col}']:,.2f} - {self.stats[f'max_{col}']:,.2f}
                </li>''' for col in self.numericColumns] + 
                [f'''
                <li class="list-group-item">
                    <strong>{col} Distribution</strong><br>
                    {''.join([f"{value}: {self.stats[f'percentage_{col}_{value}']:.1f}% ({self.stats[f'total_{col}_{value}']:,} cases)<br>"
                             for value in self.df[col].unique()])}
                </li>''' for col in self.categoricalColumns])

            plotsHtml = '\n'.join([f'<div id="{name}" class="col-md-6 mb-4"></div>'
                                 for name, _ in self.figures if not (name.startswith('scatter_') or name == 'correlation_heatmap')])
            
            correlationPlots = f'''
                <div class="col-12 mb-4">
                    <div id="correlation_heatmap" class="mb-4"></div>
                    {''.join([f'<div id="{name}" class="mb-4"></div>'
                             for name, _ in self.figures if 'scatter_' in name])}
                </div>'''

            plotsJs = '\n'.join([f"var {name}Data = {fig.to_json()}; Plotly.newPlot('{name}', {name}Data.data, {name}Data.layout);"
                                for name, fig in self.figures])

            htmlTemplate = f'''<!DOCTYPE html>
<html>
<head>
    <title>{self.datasetName} - Data Analysis Report</title>
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.1.3/dist/css/bootstrap.min.css" rel="stylesheet">
    <script src="https://cdn.jsdelivr.net/npm/bootstrap@5.1.3/dist/js/bootstrap.bundle.min.js"></script>
    <link href="https://cdn.datatables.net/1.10.24/css/dataTables.bootstrap5.min.css" rel="stylesheet">
    <script src="https://code.jquery.com/jquery-3.5.1.min.js"></script>
    <script src="https://cdn.datatables.net/1.10.24/js/jquery.dataTables.min.js"></script>
    <script src="https://cdn.datatables.net/1.10.24/js/dataTables.bootstrap5.min.js"></script>
    <script src="https://cdn.plot.ly/plotly-latest.min.js"></script>
    <style>
        body {{ padding: 20px; background-color: #f8f9fa; }}
        .card {{ margin-bottom: 20px; box-shadow: 0 0.125rem 0.25rem rgba(0,0,0,0.075); }}
        .plot-section {{ background: white; padding: 20px; border-radius: 5px; }}
        .nav-pills .nav-link {{ color: #495057; margin-right: 10px; }}
        .nav-pills .nav-link:hover {{ background-color: #e9ecef; }}
        h1 .dataset-name {{ color: #007bff; }}
    </style>
</head>
<body>
    <div class="container">
        <h1 class="text-center mb-4">Data Analysis Report<br><small class="dataset-name">{self.datasetName}</small></h1>
        <div class="card mb-4">
            <div class="card-body">
                <nav class="nav nav-pills">
                    <a class="nav-link" href="#summary">Data Summary</a>
                    <a class="nav-link" href="#findings">Key Findings</a>
                    <a class="nav-link" href="#univariate">Univariate Analysis</a>
                    <a class="nav-link" href="#bivariate">Bivariate Analysis</a>
                    <a class="nav-link" href="#quality">Data Quality</a>
                    <a class="nav-link" href="#explorer">Data Explorer</a>
                </nav>
            </div>
        </div>
        <div class="card" id="summary">
            <div class="card-body">
                <h2>Data Summary <span data-bs-toggle="tooltip" data-bs-placement="right" title="Overview of the dataset structure and composition">ℹ️</span></h2>
                <div class="row">{summaryHtml}</div>
            </div>
        </div>
        <div class="card" id="findings">
            <div class="card-body">
                <h2>Key Findings <span data-bs-toggle="tooltip" data-bs-placement="right" title="Statistical summary of all variables">ℹ️</span></h2>
                <ul class="list-group list-group-flush">{findingsHtml}</ul>
            </div>
        </div>
        <div class="card" id="univariate">
            <div class="card-body">
                <h2>Univariate Analysis <span data-bs-toggle="tooltip" data-bs-placement="right" title="Distribution and patterns of individual variables">ℹ️</span></h2>
                <div class="row">{plotsHtml}</div>
            </div>
        </div>
        <div class="card" id="bivariate">
            <div class="card-body">
                <h2>Bivariate Analysis <span data-bs-toggle="tooltip" data-bs-placement="right" title="Relationships between pairs of variables">ℹ️</span></h2>
                {correlationPlots}
            </div>
        </div>
        <div class="card" id="quality">
            <div class="card-body">
                <h2>Data Quality Report <span data-bs-toggle="tooltip" data-bs-placement="right" title="Summary of data cleaning and quality improvements">ℹ️</span></h2>
                <div class="alert alert-info">
                    <ul class="list-unstyled mb-0">{''.join([f"<li>✅ {log}</li>" for log in self.cleaningLog])}</ul>
                </div>
            </div>
        </div>
        <div class="card" id="explorer">
            <div class="card-body">
                <h2>Interactive Data Explorer <span data-bs-toggle="tooltip" data-bs-placement="right" title="Explore and search through the complete dataset">ℹ️</span></h2>
                <div class="table-responsive">{self.df.to_html(classes='table table-striped', table_id='dataTable')}</div>
            </div>
        </div>
        <div class="text-center text-muted mt-4"><small>{timestamp}</small></div>
    </div>
    <script>
        $(document).ready(function() {{
            $('#dataTable').DataTable({{pageLength: 10, order: []}});
            $('[data-bs-toggle="tooltip"]').tooltip();
        }});
        $(window).on('scroll', function() {{
            $('.card').each(function() {{
                if ($(window).scrollTop() >= $(this).offset().top - 100) {{
                    var id = $(this).attr('id');
                    $('.nav-link').removeClass('active');
                    $('.nav-link[href="#' + id + '"]').addClass('active');
                }}
            }});
        }});
        {plotsJs}
    </script>
</body>
</html>'''
            return htmlTemplate
        except Exception as e:
            print(f"Error generating report: {str(e)}")
            raise

# Script execution entry point
def main():
    try:
        print("Loading dataset...")
        if not os.path.exists(datasetUrl):
            raise FileNotFoundError(f"Dataset not found at: {datasetUrl}")
        
        datasetName = os.path.splitext(os.path.basename(datasetUrl))[0]
        reportFilename = f'{datasetName}_Analysis_Report.html'
        cleanedFilename = f'Cleaned_{datasetName}_Data.csv'
        
        df = pd.read_csv(datasetUrl)
        print(f"\nAnalyzing {datasetName} dataset...")
        
        analyzer = DataAnalyzer(df, datasetName)
        with open(reportFilename, 'w', encoding='utf-8') as f:
            f.write(analyzer.generateReport())
        df.to_csv(cleanedFilename, index=False)

        print(f"\nAnalysis completed successfully!\nGenerated files:\n1. {reportFilename} - Complete analysis report\n2. {cleanedFilename} - Processed dataset")

    except Exception as e:
        print(f"Error: {str(e)}")

if __name__ == "__main__":
    print_scribelytics_art()
    main()
