"""Python-authored interactive figures; browser only displays their JSON."""
from pathlib import Path
import sys,json
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'styles'))
import skh_palette as skh
skh.use()
import plotly.graph_objects as go

def chart(x,reference,selected,ylabel,kind='line',capacity=None):
    f=go.Figure()
    for name,values,color in [('Baseline',reference,skh.C['teal']),('Selected case',selected,skh.C['amber'])]:
        if kind=='bar':f.add_trace(go.Bar(x=x,y=values,name=name,marker_color=color))
        else:f.add_trace(go.Scatter(x=x,y=values,name=name,mode='lines+markers',line={'color':color,'width':2.5},marker={'size':7}))
    if capacity is not None:f.add_hline(y=capacity,line_color=skh.C['graphite'],line_dash='dash',line_width=2,annotation_text='Selected tank capacity',annotation_position='top left')
    f.update_layout(template='plotly_white',height=370,autosize=True,
                    margin={'l':62,'r':22,'t':42,'b':50},paper_bgcolor='rgba(0,0,0,0)',plot_bgcolor='rgba(0,0,0,0)',
                    font={'family':'Archivo, system-ui, sans-serif','color':skh.C['graphite'],'size':12},
                    legend={'orientation':'h','y':1.16,'x':0},barmode='group',yaxis_title=ylabel,
                    hovermode='x unified',colorway=skh.CATEGORICAL)
    f.update_xaxes(showgrid=False,automargin=True)
    f.update_yaxes(gridcolor=skh.C['mist'],gridwidth=.5,zeroline=False,automargin=True)
    return json.loads(f.to_json())
