import React, { useState, useEffect } from 'react'
import axios from 'axios'
import './App.scss'

import img from './img/skeleton-jumping_jack.jpg'

function App () {
  const [eaws_data, set_eaws_data] = useState([])

  const get_eaws_score = async () => {
    const resp = await axios.get('/eaws_api/v2/entities')
    set_eaws_data(resp.data)
    console.log(resp)
  }
  useEffect(() => {
    setInterval(get_eaws_score, 2000)
  }, [])

  console.log(eaws_data)
  return (
    <div className='App'>
      <img src={img} alt="Here should be jumping jack"/>
      {eaws_data.length !== 0 && (
        <>
        <section className='eaws-table'>
          <header>
            <div className='col'>Body Angle</div>
            <div className='col'>Upper Limb Angle</div>
            <div className='col'>Lower Limb Angle</div>
            <div className='col'>EAWS score</div>
          </header>
          <div className='row'>
            <div className='col'>{eaws_data[0].body_angle.value}</div>
            <div className='col'>{eaws_data[0].upper_limbs_angle.value}</div>
            <div className='col'>{eaws_data[0].lower_limbs_angle.value}</div>
            <div className='col'>{eaws_data[0].eaws_score.value}</div>
          </div>
        </section>
        <section className='shoulder_left'>Left shoulder: {eaws_data[0].upper_limbs_angle.value}</section>
        <section className='hip_left'>Hip left: {eaws_data[0].lower_limbs_angle.value}</section>
        <section className='eaws-score'>Total EAWS: {eaws_data[0].eaws_score.value}</section>
        </>
      )}
    </div>
  )
}

export default App
