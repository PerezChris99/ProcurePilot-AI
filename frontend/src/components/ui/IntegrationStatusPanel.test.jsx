import {describe,expect,it,vi} from 'vitest';
import {render,screen,within,fireEvent} from '@testing-library/react';
import IntegrationStatusPanel from './IntegrationStatusPanel.jsx';

const healthy={isSuccess:true,isError:false,isFetching:false,refetch:vi.fn()};
function row(name){return screen.getByText(name).closest('.service-row')}

describe('IntegrationStatusPanel',()=>{
  it('distinguishes connected database, missing key, partial provider and missing webhook',()=>{
    const integrations={
      isPending:false,isError:false,isFetching:false,dataUpdatedAt:0,refetch:vi.fn(),
      data:{
        database:{connected:true,schema_ready:true,engine:'sqlite'},
        ai:{configured:false,api_key_set:false,model:'gemini-3.8-flash'},
        channel3:{configured:false,api_key_set:false,base_url_configured:true},
        paypal:{environment:'sandbox',credentials_configured:false,client_id_set:true,client_secret_set:false,webhook_configured:false},
      },
    };
    render(<IntegrationStatusPanel health={healthy} integrations={integrations}/>);
    expect(within(row('SQLite')).getByText('Ready')).toBeInTheDocument();
    expect(within(row('Google Gemini')).getByText('Not configured')).toBeInTheDocument();
    expect(within(row('Channel3 catalogue')).getByText('Incomplete')).toBeInTheDocument();
    expect(within(row('PayPal Sandbox')).getByText('Incomplete')).toBeInTheDocument();
    expect(within(row('PayPal webhook')).getByText('Not configured')).toBeInTheDocument();
    expect(screen.getByText(/configured means credentials are present, not verified/i)).toBeInTheDocument();
    fireEvent.click(screen.getByRole('button',{name:'Refresh system status'}));
    expect(healthy.refetch).toHaveBeenCalledTimes(1);
    expect(integrations.refetch).toHaveBeenCalledTimes(1);
  });
  it('warns when a database migration is missing even if the connection succeeds',()=>{
    render(<IntegrationStatusPanel health={healthy} integrations={{
      isPending:false,isError:false,isFetching:false,dataUpdatedAt:0,refetch:vi.fn(),
      data:{database:{connected:true,schema_ready:false,engine:'postgresql'},ai:{},channel3:{},paypal:{environment:'unknown'}},
    }}/>);
    expect(within(row('PostgreSQL')).getByText('Migration needed')).toBeInTheDocument();
  });
});
