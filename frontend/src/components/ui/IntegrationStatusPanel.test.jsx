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
    expect(within(row('AI models · Google ADK')).getByText('Not configured')).toBeInTheDocument();
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


describe('Live PayPal webhook status and manual refresh',()=>{
  it('shows a masked configured webhook ID, stored signed delivery, and separate checkout readiness',()=>{
    render(<IntegrationStatusPanel health={healthy} integrations={{
      isPending:false,isError:false,isFetching:false,dataUpdatedAt:Date.now(),refetch:vi.fn(),
      data:{
        database:{connected:true,schema_ready:true,engine:'postgresql'},
        ai:{},channel3:{},
        paypal:{
          environment:'sandbox',credentials_configured:true,
          client_id_set:true,client_secret_set:true,
          webhook_configured:true,webhook_id_valid:true,
          webhook_id_hint:'••••771C',webhook_url_configured:true,
          webhook_last_verified_at:'2026-11-08T14:00:00Z',
          merchant_checkout_verified:false,
        },
      },
    }}/>);
    const webhook=row('PayPal webhook');
    expect(within(webhook).getByText('Configured')).toBeInTheDocument();
    expect(within(webhook).getByText(/Webhook ID ••••771C/)).toBeInTheDocument();
    expect(within(webhook).getByText(/Signed delivery recorded/)).toBeInTheDocument();
    expect(within(row('PayPal Sandbox')).getByText(/checkout not yet verified/)).toBeInTheDocument();
  });

  it('performs an explicit network refresh and reports its completion',async()=>{
    const onRefresh=vi.fn().mockResolvedValue(undefined);
    render(<IntegrationStatusPanel onRefresh={onRefresh} health={healthy} integrations={{
      isPending:false,isError:false,isFetching:true,dataUpdatedAt:0,refetch:vi.fn(),
      data:{database:{connected:true,schema_ready:true,engine:'postgresql'},paypal:{}},
    }}/>);
    const button=screen.getByRole('button',{name:'Refresh system status'});
    expect(button).toBeEnabled(); // passive polling must not block a manual refresh
    fireEvent.click(button);
    expect(onRefresh).toHaveBeenCalledTimes(1);
    expect(await screen.findByText(/Status updated just now/)).toBeInTheDocument();
    expect(button).toBeEnabled();
  });

  it('reports network failures instead of pretending configuration was freshly checked',async()=>{
    render(<IntegrationStatusPanel onRefresh={vi.fn().mockRejectedValue(new Error('offline'))}
      health={healthy} integrations={{
        isPending:false,isError:false,isFetching:false,dataUpdatedAt:0,refetch:vi.fn(),
        data:{database:{connected:true,schema_ready:true,engine:'postgresql'},paypal:{}},
      }}/>);
    fireEvent.click(screen.getByRole('button',{name:'Refresh system status'}));
    expect(await screen.findByRole('alert')).toHaveTextContent(/Refresh failed/);
  });
});

describe('AI provider backup status',()=>{
  it('shows configured Groq and OpenRouter backups without suggesting live validation',()=>{
    render(<IntegrationStatusPanel health={healthy} integrations={{
      isPending:false,isError:false,isFetching:false,dataUpdatedAt:0,refetch:vi.fn(),
      data:{
        database:{connected:true,schema_ready:true,engine:'postgresql'},
        ai:{configured:true,api_key_set:true,model:'gemini-3.5-flash-lite',
          fallback_enabled:true,backup_providers:{groq:true,openrouter:true}},
        channel3:{configured:true,api_key_set:true,base_url_configured:true},
        paypal:{environment:'sandbox',credentials_configured:true,client_id_set:true,
          client_secret_set:true,webhook_configured:false},
      },
    }}/>);
    const modelRow=row('AI models · Google ADK');
    expect(within(modelRow).getByText('Configured')).toBeInTheDocument();
    expect(within(modelRow).getByText(/Groq ready/)).toBeInTheDocument();
    expect(within(modelRow).getByText(/OpenRouter ready/)).toBeInTheDocument();
    expect(screen.getByText(/configured means credentials are present, not verified/i)).toBeInTheDocument();
  });
});
