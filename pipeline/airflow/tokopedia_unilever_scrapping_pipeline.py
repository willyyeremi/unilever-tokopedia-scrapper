from airflow import DAG
from airflow.operators.python import PythonOperator
from airflow.operators.bash_operator import BashOperator
from airflow.operators.subdag_operator import SubDagOperator
from airflow.operators.dagrun_operator import TriggerDagRunOperator
from airflow.operators.dummy_operator import DummyOperator
from airflow.utils.trigger_rule import TriggerRule

import datetime
import sys

sys.path.insert(0, '/opt/airflow/script/tokopedia_unilever_scrapping_pipeline')
import module

default_args = {
    'owner': 'airflow',
    'depends_on_past': False,
    'start_date': datetime.datetime(2023, 1, 1),
    'email_on_failure': False,
    'email_on_retry': False,
    'retries': 1,
}

def create_subdag_1(parent_dag_name, child_dag_name, args):
    dag_subdag = DAG(
        dag_id = f'{parent_dag_name}.{child_dag_name}',
        default_args = args,
        schedule_interval = '@daily',
        catchup = False,
    )

    def driver_maker_task_func():
        driver = module.scrapper.driver_maker()
        return driver

    def product_list_loader_task_func(driver, **kwargs):
        url = kwargs.get('url', 'https://www.tokopedia.com/unilever/product')
        link_list, new_url, new_state = module.scrapper.product_list_loader(driver, url)
        return link_list, new_url, new_state

    def web_data_get_task_func(driver, link_list):
        data_list = module.scrapper.web_data_get(driver, link_list)
        return data_list

    def product_master_input_task_func(data_list):
        module.scrapper.product_master_input('/home/credential.csv', data_list)

    def product_input_task_func(data_list):
        module.scrapper.product_input('/home/credential.csv', data_list)

    driver_maker_task = PythonOperator(
        task_id = 'driver_maker_task',
        python_callable = driver_maker_task_func,
        provide_context = True,
        dag = dag_subdag
    )

    product_list_loader_task = PythonOperator(
        task_id = 'product_list_loader_task',
        python_callable = product_list_loader_task_func,
        provide_context = True,
        op_kwargs = {
            'driver': '{{ task_instance.xcom_pull(task_ids = "driver_maker_task") }}',
            'url': '{{ task_instance.xcom_pull(task_ids = "product_list_loader_task[1]") }}'
        },
        dag = dag_subdag
    )

    web_data_get_task = PythonOperator(
        task_id = 'web_data_get_task',
        python_callable = web_data_get_task_func,
        provide_context = True,
        op_kwargs = {
            'driver': '{{ task_instance.xcom_pull(task_ids = "driver_maker_task") }}',
            'link_list': '{{ task_instance.xcom_pull(task_ids = "product_list_loader_task")[0] }}'
        },
        dag = dag_subdag
    )

    product_master_input_task = PythonOperator(
        task_id = 'product_master_input_task',
        python_callable = product_master_input_task_func,
        provide_context = True,
        op_kwargs = {
            'data_list': '{{ task_instance.xcom_pull(task_ids = "web_data_get_task") }}'
        },
        dag = dag_subdag
    )

    product_input_task = PythonOperator(
        task_id = 'product_input_task',
        python_callable = product_input_task_func,
        provide_context = True,
        op_kwargs = {
            'data_list': '{{ task_instance.xcom_pull(task_ids = "web_data_get_task") }}'
        },
        dag = dag_subdag
    )

    driver_maker_task >> product_list_loader_task >> web_data_get_task >> [product_master_input_task, product_input_task]

    return dag_subdag

with DAG('bfi_test_case', default_args = default_args, schedule_interval = '@daily') as dag:
    def check_state(**context):
        task_instance = context['task_instance']
        state, url = task_instance.xcom_pull(task_ids = 'subdag.product_list_loader_task')[1:3]
        if state == 1:
            return 'loop_subdag_1_task'
        return 'dummy'

    subdag_1_task = SubDagOperator(
        task_id = 'subdag_1_task',
        subdag = create_subdag_1('bfi_test_case', 'subdag_1_task', default_args),
        default_args = default_args,
        dag = dag
    )
    
    check_state_task = PythonOperator(
        task_id = 'check_state_task',
        python_callable = check_state,
        provide_context = True,
        dag = dag
    )

    loop_subdag_1_task = TriggerDagRunOperator(
        task_id = 'loop_subdag_1_task',
        trigger_dag_id = 'bfi_test_case',
        execution_date = '{{ execution_date }}',
        reset_dag_run = True,
        wait_for_completion = True,
        trigger_rule = TriggerRule.ALL_DONE,
        dag = dag
    )
    
    pricerecommendation_ml_task = BashOperator(
        task_id='pricerecommendation_ml_task',
        bash_command='python /opt/airflow/script/tokopedia_unilever_scrapping_pipeline/pricerecommendation.py',
        dag=dag,
    )

    subdag_1_task >> check_state_task 
    check_state_task >> [loop_subdag_1_task, pricerecommendation_ml_task]